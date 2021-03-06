import pymongo
from bson.objectid import ObjectId
import re
import settings
import json
from lib import sanitize
from datetime import datetime
from datetime import date
from datetime import timedelta
from mongoengine import *
from lib.userdb import User
from lib.custom_fields import ImprovedStringField, ImprovedURLField
from mongo import db
from slugify import slugify
from lib.commentsdb import Comment

#
# Post Object
#
class Post(Document):
    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        db = self._get_db()
    meta = {
        'indexes': ['slug', 'date_created', 'votes', 'disqus_comment_count']
    }
    date_created = DateTimeField(required=True, default=datetime.now())
    title = StringField(required=True)
    slugs = ListField(StringField())
    slug = StringField()
    user = EmbeddedDocumentField(User, required=True)
    tags = ListField(ImprovedStringField())
    topic_slug = StringField()
    url = ImprovedURLField(max_length=65000, required=False) # link to external content (if any)
    normalized_url = ImprovedStringField(max_length=65000, required=False)
    hackpad_url = ImprovedURLField(max_length=65000)
    has_hackpad = BooleanField(default=False)
    body_raw = ImprovedStringField(required=False)
    body_html = ImprovedStringField(required=False)
    body_truncated = ImprovedStringField(required=False)
    body_text = ImprovedStringField(required=False)
    status = StringField(default="new")
    featured = BooleanField(default=False)
    date_featured = DateTimeField()
    voted_users = ListField(EmbeddedDocumentField(User))
    votes = IntField()
    deleted = IntField()
    date_deleted = DateTimeField()
    sort_score = IntField()
    daily_sort_score = FloatField()
    downvotes = IntField()
    super_upvotes = IntField()
    super_downvotes = IntField()
    subscribed = ListField(EmbeddedDocumentField(User))
    domain = StringField()
    disqus_thread_id_str = StringField()
    disqus_comment_count = IntField()

    def __str__(self):
        try:
            return 'Post: "%s" by %s' % (self.title, self.user.screen_name)
        except:
            return 'Empty Post'

    def add_slug(self, title):
        slug = slugify(title)
        counter_coll = self._get_collection_name() + 'Slug'
        counter = self._get_db()[counter_coll].find_and_modify(query={'_id': slug},
                                                                update={'$inc': {'value': 1}},
                                                                upsert=True, new=True)
        if counter['value'] != 1:
            slug = '%s-%i' % (counter['_id'], counter['value'])
        self._data['slugs'] = self._data.get('slugs', []) + [slug]
        self._data['slug'] = slug
        return slug

    def save(self, *args, **kwargs):
        self.validate()
        title_changed = hasattr(self, '_changed_fields') and 'title' in self._changed_fields
        if (title_changed or not self._data.get('slug')) and len(self._data.get('slugs', [])) < 6:
            try:
                self.add_slug(unicode(self._data['title']))
            except:
                self.add_slug(unicode(self._data['title'].decode('utf-8')))
            if hasattr(self, '_changed_fields'):
                self._changed_fields += ['slug', 'slugs']
        super(Post, self).save(*args, **kwargs)

    def set_fields(self, **kwargs):
        for fname in self._fields.keys():
            if kwargs.has_key(fname):
                setattr(self, fname, kwargs[fname])

    def permalink(self):
        return "/posts/%s" % self._data['slug']

    def editlink(self):
        return "%s/edit" % self.permalink()

    def invitelink(self):
        return "%s/invite" % self.permalink()

    def comment_count(self):
        return len(Comment.objects(post=self))
        #return "5"

    def dblink(self):
        return "%s/post/%s" % (settings.get('db_edit_baseurl'), self._data['id'])

    def add_comment_link(self):
        return self.permalink() + "/add_comment"

    def add_slug(self, title):
        slug = slugify(title)
        counter_coll = self._get_collection_name() + 'Slug'
        counter = self._get_db()[counter_coll].find_and_modify(query={'_id': slug},
                                                                update={'$inc': {'value': 1}},
                                                                upsert=True, new=True)
        if counter['value'] != 1:
            slug = '%s-%i' % (counter['_id'], counter['value'])
        self._data['slugs'] = self._data.get('slugs', []) + [slug]
        self._data['slug'] = slug
        return slug

###########################
### GET ALL POSTS
###########################
def get_all():
    return db.post.find()

###########################
### GET A SPECIFIC POST
###########################
def get_post_by_slug(slug):
    return Post.objects(slug=slug).first()

def get_post_by_id(post_id):
    return Post.objects(id=post_id).first()

def get_all():
    return Post.objects()

###########################
### GET PAGED LISTING OF POSTS
###########################
def get_posts_by_bumps(screen_name, per_page, page):
    return Post.objects(voted_users__screen_name=screen_name, user__screen_name__ne=screen_name).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

def get_posts_by_query(query, per_page=10, page=1):
    query_regex = re.compile('%s[\s$]' % query, re.I)
    return Post.objects(__raw__={'$or':[{'title':query_regex}, {'body_raw':query_regex}]}).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

def get_posts_by_tag(tag):
    return Post.objects(deleted__ne=True, tags__in=[tag]).order_by('-date_created')

def get_posts_by_topic(topic_slug):
    return Post.objects(deleted__ne=True, topic_slug=topic_slug).order_by('-date_created')

def get_essentials_by_topic(topic_slug):
    return Post.objects(deleted__ne=True, topic_slug=topic_slug).order_by('-votes')

def get_essentials_by_tag(tag):
    return Post.objects(deleted__ne=True, tags__in=[tag]).order_by('-votes')

def get_posts_by_screen_name(screen_name, per_page=10, page=1):
    return Post.objects(deleted__ne=True, user__screen_name=screen_name).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

def get_posts_by_screen_name_and_tag(screen_name, tag, per_page=10, page=1):
    return Post.objects(deleted__ne=True, user__screen_name=screen_name, tags__in=[tag]).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

def get_featured_posts(per_page=10, page=1):
    today = datetime.today()
    week_ago = today - timedelta(days=3)
    return Post.objects(deleted__ne=True, featured=True).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

def get_new_posts(per_page=50, page=1):
    return Post.objects(deleted__ne=True).order_by('-date_created').limit(per_page).skip((page-1)*per_page)

def get_hot_posts_by_day(day=date.today(), hide_featured=False):
    day = datetime.combine(day, datetime.min.time())
    day_plus_one = day + timedelta(days=1)
    if hide_featured:
        posts = Post.objects(deleted__ne=True, featured__ne=True, date_created__gte=day, date_created__lte=day_plus_one).order_by('-daily_sort_score')
    else:
        posts = Post.objects(deleted__ne=True, date_created__gte=day, date_created__lte=day_plus_one).order_by('-daily_sort_score')
    return posts

def get_daily_posts_by_sort_score(min_score=8):
    day=date.today()
    day = datetime.combine(day, datetime.min.time())
    day_plus_one = day + timedelta(days=1)
    return list(db.post.find({'daily_sort_score': {"$gte" : min_score }, "deleted": { "$ne": True }, 'date_created': {'$gte': day, '$lte': day_plus_one}}, sort=[('daily_sort_score', pymongo.DESCENDING)]))

def get_hot_posts_24hr(start=datetime.now()):
    end = start - timedelta(hours=24)
    return Post.objects(deleted__ne=True, date_created__gte=end, date_created__lte=start).order_by('-daily_sort_score')

def get_sad_posts(per_page=50, page=1):
    return Post.objects(date_created__gt=datetime.strptime("10/12/13", "%m/%d/%y"), votes=1, comment_count=0, deleted__ne=True, featured__ne=True).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

def get_deleted_posts(per_page=50, page=1):
    return Post.objects(deleted=True).order_by('-date_created').skip((page-1)*per_page).limit(per_page)

###########################
### AGGREGATE QUERIES
###########################
def get_unique_posters(start_date, end_date):
    """
    Original query: return db.post.group(["user.screen_name"], {'date_created':{'$gte': start_date, '$lte': end_date}}, {"count":0}, "function(o, p){p.count++}" )
    Using MongoEngine necessitating breaking out the logic
    """
    # Get all posts created in a given time period
    posts = Post.objects(date_created__gte=start_date, date_created__lte=end_date)

    # Determine unique authors of this subset of posts
    unique_posters = []
    for p in posts:
        if not any(p.user.screen_name == entry['user.screen_name'] for entry in unique_posters):
            unique_posters.append(
                {'count':len(Post.objects(user__screen_name=p.user.screen_name, date_created__gte=start_date, date_created__lte=end_date)), 
                'user.screen_name':p.user.screen_name})

    return unique_posters
    

###########################
### GET POST COUNTS
###########################
def get_featured_posts_count():
    """
    Returns number of posts that have been featured
    #return len(list(db.post.find({'featured':True})))
    """
    return len(Post.objects(featured=True))
    

def get_post_count_by_query(query):
    """
    Returns numbers of posts matching an arbitrary query
    Executes using a raw mongodb query through MongoEngine
    #return len(list(db.post.find({'$or':[{'title':query_regex}, {'body_raw':query_regex}]})))
    """
    query_regex = re.compile('%s[\s$]' % query, re.I)
    return len(Post.objects(__raw__={'$or':[{'title':query_regex}, {'body_raw':query_regex}]}))

def get_post_count():
    """
    Get total number of posts. Arbitrarily set beginning of time to 10/12/13
    to ignore posts that came before this
    #return len(list(db.post.find({'date_created':{'$gt': datetime.datetime.strptime("10/12/13", "%m/%d/%y")}})))
    """
    return len(Post.objects(date_created__gte=datetime.datetime.strptime("10/12/13", "%m/%d/%y")))

def get_post_count_for_range(start_date, end_date):
    """
    Return number of posts created within a date get_post_count_for_range
    #return len(list(db.post.find({'date_created':{'$gte': start_date, '$lte': end_date}})))
    """
    return len(Post.objects(date_created__gte=state_date, date_created__lte=end_date))

def get_delete_posts_count():
    """"
    Returns number of posts that have been deleted
    #return len(list(db.post.find({'deleted':True})))
    """
    return len(Post.objects(deleted=True))

def get_post_count_by_tag(tag):
    """
    Returns number of posts with a given tag
    #return len(list(db.post.find({'tags':tag})))
    """
    return len(Post.objects(tags__in=tag))

###########################
### GET LIST OF POSTS BY CRITERIA
###########################
def get_latest_staff_posts_by_tag(tag, limit=10):
    staff = settings.get('staff')
    return Post.objects(deleted__ne=True, user__username__in=staff, tags__in=[tag]).order_by('-date_featured').limit(limit)

def get_posts_by_normalized_url(normalized_url, limit):
    return Post.objects(normalized_url=normalized_url, deleted__ne=True).order_by('-date_created').limit(limit)

def get_posts_with_min_votes(min_votes):
    return Post.objects(deleted__ne=True, votes__gte=min_votes).order_by('-date_created')

def get_hot_posts_past_week():
    yesterday = datetime.today() - timedelta(days=1)
    week_ago = datetime.today() - timedelta(days=5)
    return Post.objects(deleted__ne=True, date_created__lte=yesterday, date_created__gte=week_ago).order_by('-daily_sort_score')[:5]

def get_related_posts_by_tag(tag):
    return Post.objects(deleted__ne=True, tags__in=tag).order_by('-daily_sort_score')[:2]

###########################
### UPDATE POST DETAIL
###########################
def delete_all_posts_by_user(screen_name):
    posts = get_posts_by_screen_name(screen_name, 1000, 1)
    posts.update(set__deleted=True, set__date_deleted=datetime.datetime.utcnow())

###########################
### ADD A NEW POST
###########################
def insert_post(post_dict):
    slug = slugify(post_dict['title'])
    slug_count = len(list(db.post.find({'slug':slug})))
    if slug_count > 0:
        slug = '%s-%i' % (slug, slug_count)
    post_dict['slug'] = slug
    post_dict['slugs'] = [slug]
    if 'subscribed' not in post_dict.keys():
        post_dict['subscribed'] = []
    post = Post(**post_dict)
    post.save()
    return post

def save_post(post):
    post.save()
    return

###########################
### SORT ALL POSTS
### RUN BY HEROKU SCHEDULER EVERY 5 MIN
### VIA SCRIPTS/SORT_POSTS.PY
###########################
def sort_posts(day="all"):
    # set our config values up
    staff_bonus = -3
    comments_multiplier = 3.0
    votes_multiplier = 1.0
    super_upvotes_multiplier = 3.0
    super_downvotes_multiplier = 3.0

    if day == "all":
        posts = get_all()
    else:
        posts = get_hot_posts_by_day(day)

    for post in posts:
        # determine if we should assign a staff bonus or not
        if post['user']['username'] in settings.get('staff'):
            staff_bonus = staff_bonus
        else:
            staff_bonus = 0

        # determine how to weight votes
        votes_base_score = 0
        if post['votes'] == 1 and post['comment_count'] > 2:
            votes_base_score = -2
        if post['votes'] > 8 and post['comment_count'] == 0:
            votes_base_score = -2

        if 'super_upvotes' in post.keys():
            super_upvotes = post['super_upvotes']
        else:
            super_upvotes = 0
        #super_upvotes = post.get('super_upvotes', 0)
        super_downvotes = post.get('super_downvotes', 0)

        # calculate the sub-scores
        scores = {}
        scores['votes'] = (votes_base_score + post['votes'] * votes_multiplier)
        scores['super_upvotes'] = (super_upvotes * super_upvotes_multiplier)
        scores['super_downvotes'] = (super_downvotes * super_downvotes_multiplier * -1)
        scores['comments'] = (post['comment_count'] * comments_multiplier)

        # add up the scores
        total_score = 0
        total_score += staff_bonus
        for score in scores:
            total_score += scores[score]

        # and save the new score
        post['scores'] = scores
        update_post_score(post['slug'], total_score, scores)
        print post['slug']
        print "-- %s" % total_score
        print "---- %s" % json.dumps(scores, indent=4)

    print "All posts sorted!"

###########################
### UPDATES USER DATA FOR ALL POSTS
### RUN VIA SCRIPTS/UPDATE_POSTS_USER_DATA.PY
###########################
def update_posts_user_data():
    print "Updating user data for all posts..."
    for post in get_all():
        # user
        try:
            user = post['user']
            if user:
                new_user = userdb.get_user_by_id_str(user['id_str'])
                post['user'] = new_user['user']
        except:
            print "Failed to update user for post of slug %s" % post['slug']

        # voted_users
        try:
            voted_users = post['voted_users']
            new_voted_users = []
            for voted_user in voted_users:
                new_voted_user = userdb.get_user_by_id_str(voted_user['id_str'])
                if new_voted_user:
                    new_voted_users.append(new_voted_user['user'])
            post['voted_users'] = new_voted_users
        except:
            print "Failed to update voted_users for post of slug %s" % post['slug']

        # Save post
        save_post(post)

    print "Finished updating user data for all posts"
