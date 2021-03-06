#-*- coding:utf-8 -*-
import app.basic

import logging
import re
import settings
import tornado.web
import tornado.options
import urllib
from slugify import slugify
import datetime
import time
from urlparse import urlparse
from lib import bitly
from lib import google
from lib import mentionsdb
from lib import commentsdb
from lib import postsdb
from lib import sanitize
from lib import tagsdb
from lib import userdb
from lib import disqus
from lib import topicsdb
from lib import template_helpers
from lib.postsdb import Post
from lib.userdb import User
from customerio import CustomerIO
cio = CustomerIO(settings.get('customer_io_site_id'), settings.get('customer_io_api_key'))

###############
### New Post
### /posts/new
###############
class NewPost(app.basic.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        post = Post()
        post.title = self.get_argument('title', '')
        post.url = self.get_argument('url', '')
        is_bookmarklet = False
        if self.request.path.find('/bookmarklet') == 0:
            is_bookmarklet = True

        self.render('post/new_post.html', submit_post=post, is_bookmarklet=is_bookmarklet)

###############
### Edit Post Form
### /posts/([^\/]+)/edit
###############
class EditPost(app.basic.BaseHandler):
    @tornado.web.authenticated
    def get(self, slug):
        post = postsdb.get_post_by_slug(slug)
        if post and post.user.screen_name == self.current_user or self.current_user_can('edit_posts'):
            # available to edit this post
            self.render('post/edit_post.html', post=post)
        else:
            # not available to edit right now
            self.redirect('/posts/%s' % slug)


###############
### Process a Create or Update
### /posts/create_update
###############
class CreateUpdatePost(app.basic.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        sort_by = self.get_argument('sort_by', 'hot')
        page = abs(int(self.get_argument('page', '1')))
        per_page = abs(int(self.get_argument('per_page', '9')))
        is_blacklisted = False
        msg = 'success'
        if self.current_user:
            is_blacklisted = self.is_blacklisted(self.current_user)

        post = {}
        post['slug'] = self.get_argument('slug', None)
        post['title'] = self.get_argument('title', '')
        post['url'] = self.get_argument('url', '')
        post['body_raw'] = self.get_argument('body_raw', '')
        post['tags'] = self.get_argument('tags', '').split(',')
        post['featured'] = self.get_argument('featured', '')
        post['has_hackpad'] = self.get_argument('has_hackpad', '')
        post['slug'] = self.get_argument('slug', '')
        post['sort_score'] = 0
        post['daily_sort_score'] = 0

        # handle topics
        if self.get_argument('primary_topic', '') == "" or self.get_argument('primary_topic', '') == "+other+":
            post['topic_slug'] = slugify(unicode(self.get_argument('secondary_topic', '')))
        else:
            post['topic_slug'] = self.get_argument('primary_topic', '')

        if post['has_hackpad'] != '':
            post['has_hackpad'] = True
        else:
            post['has_hackpad'] = False

        deleted = self.get_argument('deleted', '')
        if deleted != '':
            post['deleted'] = True
            post['date_deleted'] = datetime.datetime.now()

        bypass_dup_check = self.get_argument('bypass_dup_check', '')
        is_edit = False
        if post['slug']:
            bypass_dup_check = "true"
            is_edit = True

        dups = []

        # make sure user isn't blacklisted
        if not self.is_blacklisted(self.current_user):
            # check if there is an existing URL
            if post['url'] != '':
                url = urlparse(post['url'])
                netloc = url.netloc.split('.')
                if netloc[0] == 'www':
                    del netloc[0]
                path = url.path
                if path and path[-1] == '/':
                    path = path[:-1]
                url = '%s%s' % ('.'.join(netloc), path)
                post['normalized_url'] = url

                long_url = post['url']
                if long_url.find('goo.gl') > -1:
                    long_url = google.expand_url(post['url'])
                if long_url.find('bit.ly') > -1 or long_url.find('bitly.com') > -1:
                    long_url = bitly.expand_url(post['url'].replace('http://bitly.com','').replace('http://bit.ly',''))
                post['domain'] = urlparse(long_url).netloc

            ok_to_post = True

            dups = postsdb.get_posts_by_normalized_url(post.get('normalized_url', ""), 1)
            if post['url'] != '' and len(dups) > 0 and bypass_dup_check != "true":
                ##
                ## If there are dupes, kick them back to the post add form
                ##
                return (self.render('post/new_post.html', post=post, dups=dups))

            # Handle tags
            post['tags'] = [t.strip().lower() for t in post['tags']]
            post['tags'] = [t for t in post['tags'] if t]
            userdb.add_tags_to_user(self.current_user, post['tags'])
            for tag in post['tags']:
                tagsdb.save_tag(tag)

            # format the content as needed
            post['body_html'] = sanitize.html_sanitize(post['body_raw'], media=self.current_user_can('post_rich_media'))
            post['body_text'] = sanitize.html_to_text(post['body_html'])
            post['body_truncated'] = sanitize.truncate(post['body_text'], 500)

            # determine if this should be a featured post or not
            if self.current_user_can('feature_posts') and post['featured'] != '':
                post['featured'] = True
                post['date_featured'] = datetime.datetime.now()
            else:
                post['featured'] = False
                post['date_featured'] = None

            user_info = userdb.get_user_by_screen_name(self.current_user)
            
            if not post['slug'] or post.get('slug') == "" or post.get('slug') == "None":
                # No slug -- this is a new post.
                # initiate fields that are new
                post['disqus_shortname'] = settings.get('disqus_short_code')
                post['muted'] = False
                post['comment_count'] = 0
                post['disqus_thread_id_str'] = ''
                post['sort_score'] = 0.0
                post['downvotes'] = 0
                post['hackpad_url'] = ''
                post['date_created'] = datetime.datetime.now()
                post['user'] = user_info.user
                post['votes'] = 1
                post['voted_users'] = [user_info.user]
                #save it
                saved_post = postsdb.insert_post(post)
                print "new post"

                # send notification to customer.io
                # if post is in a topic
                if saved_post.topic_slug != "":
                    topic = topicsdb.get_topic_by_slug(saved_post.topic_slug)
                    data ={
                        'topic_name': topic.name,
                        'post_author': saved_post.user.username,
                        'post_title': saved_post.title,
                        'post_permalink': saved_post.permalink(),
                        'post_id': str(saved_post.id)
                    }
                    # find topic followers
                    followers = userdb.get_followers(topic.slug)
                    # for each follower, ping customer.io about this post.
                    for follower in followers:
                        cio.track(customer_id=follower.user.username, name='new_post_notification', **data)

            else:
                # this is an existing post.
                print "existing post"
                # attempt to edit the post (make sure they are the author)
                saved_post = postsdb.get_post_by_slug(post['slug'])
                if saved_post:
                    if self.current_user == saved_post['user']['screen_name'] or self.current_user_can('edit_posts'):
                        # looks good - let's update the saved_post values to new values
                        for key in post.keys():
                            saved_post[key] = post[key]
                        # finally let's save the updates
                        postsdb.save_post(saved_post)
                        msg = 'success'
                if saved_post and self.current_user == saved_post['user']['screen_name']:
                    # looks good - let's update the saved_post values to new values
                    saved_post.set_fields(**post)
                    # finally let's save the updates
                    saved_post.save()
                    msg = 'success'
            
            #
            # From here on out, we have a saved_post, which is a mongoengine Post object.
            #
            # log any @ mentions in the post
            mentions = re.findall(r'@([^\s]+)', saved_post.body_raw)
            for mention in mentions:
                mentionsdb.add_mention(mention.lower(), saved_post.slug)

        if is_edit:
            self.set_secure_cookie('flash', 'Edited!')
            self.redirect(saved_post.permalink())
        else:
            self.set_secure_cookie('flash', 'Nice one!')
            self.redirect(saved_post.permalink())

########################
### VIEW A SPECIFIC POST
### /post/(.+)
########################
class ViewPost(app.basic.BaseHandler):
    def get(self, slug):
        post = postsdb.get_post_by_slug(slug)
        if not post:
            raise tornado.web.HTTPError(404)

        topics = topicsdb.get_all()
        comments = commentsdb.get_comments_by_post(post)

        current_user_can_edit = False
        current_user = userdb.get_user_by_screen_name(self.current_user)
        if current_user:
            current_user_can_edit = (current_user.role == "staff" or post.user == current_user.user)
        
        # remove dupes from voted_users
        voted_users = []
        for i in post.voted_users:
            if i not in voted_users:
                voted_users.append(i)
        post.voted_users = voted_users

        self.vars.update({
            'post': post,
            'comments': comments,
            'topics': topics,
            'current_user_can_edit': current_user_can_edit
            })
        self.render('post/view_post.html', **self.vars)

##############
### Homepage
### /
##############
class ListPosts(app.basic.BaseHandler):
    def get(self, day="today", page=1, sort_by="hot"):
        view = "list"
        sort_by = self.get_argument('sort_by', sort_by)
        page = abs(int(self.get_argument('page', page)))
        per_page = abs(int(self.get_argument('per_page', '20')))
        msg = self.get_argument('msg', '')
        slug = self.get_argument('slug', '')
        new_post = None
        featured_topics = topicsdb.get_featured()

        if slug:
            new_post = postsdb.get_post_by_slug(slug)

        featured_posts = postsdb.get_featured_posts(1)
        posts = []
        hot_tags = tagsdb.get_hot_tags()

        is_today = False
        if day == "today":
            is_today = True
            day = datetime.datetime.today()
        else:
            day = datetime.datetime.strptime(day, "%Y-%m-%d")

        show_day_permalink = True
        infinite_scroll = False
        if self.request.path == ('/'):
            show_day_permalink = False
            infinite_scroll = True

        is_blacklisted = False
        if self.current_user:
            is_blacklisted = self.is_blacklisted(self.current_user)
            
        posts = postsdb.get_hot_posts_24hr(day)
        previous_day_posts = postsdb.get_hot_posts_24hr(datetime.datetime.now() - datetime.timedelta(hours=24))

        midpoint = 7
        #midpoint = (len(posts) - 1) / 2
        # midpoint determines where post list breaks from size=md to size=sm
        hot_posts_past_week = postsdb.get_hot_posts_past_week()

        self.vars.update({
          'is_today': is_today,
          'view': view,
          'posts': posts,
          'previous_day_posts': previous_day_posts,
          'hot_posts_past_week': hot_posts_past_week,
          'day': day,
          'show_day_permalink': show_day_permalink,
          'infinite_scroll': infinite_scroll,
          'new_post': new_post,
          'msg': msg,
          'featured_posts': featured_posts,
          'midpoint': midpoint,
          'featured_topics': featured_topics
        })
        self.render('post/list_posts.html', **self.vars)

##################
### FEATURED POSTS
### /featured.*$
##################
class FeaturedPosts(app.basic.BaseHandler):
    def get(self, tag=None):
        featured_posts = postsdb.get_featured_posts(1000, 1)
        tags_alpha = tagsdb.get_all_tags(sort="alpha")
        tags_count = tagsdb.get_all_tags(sort="count")

        self.render('search/search_results.html', tag=tag, tags_alpha=tags_alpha, tags_count=tags_count, posts=featured_posts, total_count=len(featured_posts), query="featured_posts", view="featured")

##############
### RSS FEED
### /feed
##############
class Feed(app.basic.BaseHandler):
    def get(self, feed_type="hot"):
        #action = self.get_argument('action', '')
        page = abs(int(self.get_argument('page', '1')))
        per_page = abs(int(self.get_argument('per_page', '9')))

        posts = []
        if feed_type == 'new':
            # show the newest posts
            posts = postsdb.get_new_posts(per_page, page)
        elif feed_type == 'sad':
            # show the sad posts
            posts = postsdb.get_sad_posts(per_page, page)
        elif feed_type == 'hot':
            # show the sad posts
            posts = postsdb.get_daily_posts_by_sort_score(8)
        elif feed_type == 'superhot':
            # show the sad posts
            posts = postsdb.get_daily_posts_by_sort_score(30)
        elif feed_type == 'superduperhot':
            # show the sad posts
            posts = postsdb.get_daily_posts_by_sort_score(50)
        elif feed_type == 'today':
            posts = postsdb.get_hot_posts_24hr()
        else:
            posts = postsdb.get_hot_posts_24hr()

        self.render('post/feed.xml', posts=posts)


##############
### List all New Posts
### /new
##############
class ListPostsNew(app.basic.BaseHandler):
    def get(self, page=1):
        page = abs(int(self.get_argument('page', page)))
        per_page = abs(int(self.get_argument('per_page', '100')))

        featured_posts = postsdb.get_featured_posts(5, 1)
        posts = []
        post = {}
        hot_tags = tagsdb.get_hot_tags()

        is_blacklisted = False
        if self.current_user:
            is_blacklisted = self.is_blacklisted(self.current_user)

        posts = postsdb.get_new_posts(per_page=per_page, page=page)

        self.vars.update({
          'posts': posts,
          'featured_posts': featured_posts,
          #'featured_posts': featured_posts,
          'is_blacklisted': is_blacklisted,
          'tags': hot_tags,
        })
        self.render('post/list_new_posts.html', **self.vars)



##########################
### Bump Up A SPECIFIC POST
### /posts/([^\/]+)/bump
##########################
class Bump(app.basic.BaseHandler):
    def get(self, slug):
        # nothing to see here
        return
    def post(self, slug):
        # user must be logged in
        msg = {}
        if not self.current_user:
            msg = {'error': 'You must be logged in to bump.', 'redirect': True}
        else:
            post = postsdb.get_post_by_slug(slug)
            if post:
                can_vote = True
                for u in post['voted_users']:
                    if u['username'] == self.current_user:
                        can_vote = False
                if not can_vote:
                    msg = {'error': 'You have already upvoted this post.'}
                else:
                    user_info = userdb.get_user_by_screen_name(self.current_user)

                    # Increment the vote count
                    post.votes += 1
                    post.update(push__voted_users=user_info.user)
                    post.save()
                    msg = {'votes': post.votes}

                    # send email notification to post author
                    author = userdb.get_user_by_screen_name(post.user.username)
                    if author.email_address:
                        subject = "[#theconversation] @%s just bumped up your post: %s" % (self.current_user, post.title)
                        text = "Woo!\n\n%s" % post.permalink()
                        logging.info('sent email to %s' % author.email_address)
                        self.send_email(settings.get('system_email_address'), author.email_address, subject, text)
        self.api_response(msg)

##########################
### Super Upvote
### /posts/([^\/]+)/superupvote
##########################
class SuperUpVote(app.basic.BaseHandler):
    def post(self, slug):
        # user must be logged in
        msg = {}
        if not self.current_user:
            msg = {'error': 'You must be logged in to super upvote.', 'redirect': True}
        elif not self.current_user_can('super_upvote'):
            msg = {'error': 'You are not authorized to super upvote', 'redirect': True}
        else:
            post = postsdb.get_post_by_slug(slug)
            if post:
                    # Increment the vote count
                post.super_upvotes += 1
                post.save()
                msg = {'supervotes': post.super_upvotes}

        self.api_response(msg)

##########################
### Super DownVote
### /posts/([^\/]+)/superdownvote
##########################
class SuperDownVote(app.basic.BaseHandler):
    def post(self, slug):
        # user must be logged in
        msg = {}
        if not self.current_user:
            msg = {'error': 'You must be logged in to super downvote.', 'redirect': True}
        elif not self.current_user_can('super_downvote'):
            msg = {'error': 'You are not authorized to super downvote', 'redirect': True}
        else:
            post = postsdb.get_post_by_slug(slug)
            if post:
                # Increment the vote count
                post.super_downvotes += 1
                post.save()
                msg = {'supervotes': post.super_downvotes}

        self.api_response(msg)

##########################
### Un-Bump A SPECIFIC POST
### /posts/([^\/]+)/unbump
##########################
class UnBump(app.basic.BaseHandler):
    def post(self, slug):
        # user must be logged in
        msg = {}
        if not self.current_user:
            msg = {'error': 'You must be logged in to bump.', 'redirect': True}
        else:
            post = postsdb.get_post_by_slug(slug)
            if post:
                can_vote = True
                for u in post['voted_users']:
                    if u['username'] == self.current_user:
                        can_unbump = True
                if not can_unbump:
                    msg = {'error': "You can't unbump this post!"}
                else:
                    user_info = userdb.get_user_by_screen_name(self.current_user)
                    post.votes -= 1
                    post.update(pull_voted_users=user_info.user)
                    post.save()
                    msg = {'votes': post.votes}

        self.api_response(msg)

#############
### WIDGET
### /widget.*?
#############
class Widget(app.basic.BaseHandler):
    def get(self, extra_path=''):
        view = self.get_argument('view', 'sidebar')
        if extra_path != '':
            self.render('post/widget_demo.html')
        else:
            # list posts
            num_posts =abs(int(self.get_argument('num_posts', '5')))

            # get the current hot posts
            day = datetime.datetime.today()
            posts = postsdb.get_hot_posts_by_day(day)
            addl_posts = []
            if len(posts) < 5:
                yesterday = day - datetime.timedelta(days=1)
                addl_posts = postsdb.get_hot_posts_by_day(yesterday)
            all_posts = posts + addl_posts
            if view == "sidebar":
                # get the current hot posts
                posts = postsdb.get_hot_posts_24hr()
                self.render('post/widget.js', posts=posts, num_posts=num_posts)
            else:
                posts = postsdb.get_hot_posts_24hr()
                self.render('post/widget_inline.js', posts=posts, num_posts=3)

###################
### WIDGET DEMO
### /widget/demo.*?
###################
class WidgetDemo(app.basic.BaseHandler):
    def get(self, extra_path=''):
        self.render('post/widget_demo.html')