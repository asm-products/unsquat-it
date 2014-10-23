import pymongo
import re
import settings
import json
from datetime import datetime
from datetime import date
from datetime import timedelta
from urlparse import urlparse
from slugify import slugify
from mongoengine import *
from lib import sanitize
from decimal import *
from lib.template_helpers import *
from lib.custom_fields import ImprovedStringField, ImprovedURLField
from lib.userdb import User

from customerio import CustomerIO
cio = CustomerIO(settings.get('customer_io_site_id'), settings.get('customer_io_api_key'))

#
# Embedded Comment
#
class Comment(Document):
    meta = {
        'indexes': ['full_slug', 'post', 'date_created']
    }
    firebase_id = StringField()
    post = ReferenceField('Post')
    parent_comment = ReferenceField('Comment')
    slug = StringField()
    full_slug = StringField()
    date_created = DateTimeField(required=True)
    author_email = StringField()
    user = EmbeddedDocumentField(User, required=True)
    body_raw = ImprovedStringField(required=False, default="")
    body_text = ImprovedStringField(required=False, default="")
    body_html = ImprovedStringField(required=False, default="")
    status = StringField(default="published")
    depth = IntField(default=1)
    
    def permalink(self):
        return "%s/comments/%s" % (settings.get('base_url'), self._data['slug'])

    def set_fields(self, **kwargs):
        for fname in self._fields.keys():
            if kwargs.has_key(fname):
                setattr(self, fname, kwargs[fname])

###########################
### Add a comment to an existing post
###########################
def add_comment(post, user_info, comment_text, parent_comment, firebase_id=None):
    comment_dict = {}
    comment_dict['firebase_id'] = firebase_id
    comment_dict['author_email'] = user_info['email_address']
    comment_dict['body_raw'] = comment_text
    comment_dict['body_html'] = sanitize.html_sanitize(comment_dict['body_raw'], media=False)
    comment_dict['body_text'] = sanitize.html_to_text(comment_dict['body_html'])
    comment_dict['user'] = user_info['user']
    comment_dict['date_created'] = datetime.datetime.now()
    # generate the unique portions of the slug and full_slug
    
    # instantiate the base comment
    comment = Comment()
    comment.set_fields(**comment_dict)
    comment.post = post
    
    slug_part = generate_slug()
    full_slug_part = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M.%S') + ':' + slug_part
    
    if parent_comment:
        comment.parent_comment = parent_comment
        comment.slug = parent_comment.slug + '/' + slug_part
        comment.full_slug = parent_comment.full_slug + '/' + full_slug_part
    else:
        comment.slug = slug_part
        comment.full_slug = full_slug_part
    
    comment.depth = len(comment.full_slug.split('/'))

    comment.save()
    
    # send comment notifications
    notify_recipients = []
    post_comments = get_comments_by_post(post)
    for comment in post_comments:
        # don't dupe people and don't send a user email about their own comment
        if comment.user.username not in notify_recipients and comment.user.username != user_info.user.username and post.user.username != comment.user.username:
            notify_recipients.append(comment.user.username)
    if post.user.username != user_info.user.username:
        notify_recipients.append(post.user.username)
    data ={
        'comment_text': comment.body_text,
        'comment_permalink': comment.permalink(),
        'comment_slug': comment.slug,
        'comment_author': comment.user.username,
        'post_title': post.title,
        'post_permalink': post.permalink(),
        'post_id': str(post.id)
    }
    for recipient in notify_recipients:
        cio.track(customer_id=recipient, name='comment_notification', **data)
    return comment

###########################
### GET LISTS OF COMMENTS
###########################

def get_comments_by_post(post):
    # Comment.objects(post=post).order_by('full_slug')
    return Comment.objects(post=post).order_by('date_created')

###########################
### GET A SPECIFIC COMMENT
###########################
def get_comment_by_id(comment_id):
    return Comment.objects(id=comment_id).first()
  
def get_comment_by_slug(comment_slug):
    return Comment.objects(slug=comment_slug).first() 