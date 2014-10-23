import pymongo
import settings
from mongo import db
from mongoengine import *

# For update_twitter
import tweepy
import urllib2
from datetime import datetime

class User(EmbeddedDocument):
    id_str = StringField(required=True)
    auth_type = StringField(required=True)
    username = StringField(required=True)
    fullname = StringField(required=True)
    screen_name = StringField(required=True)
    profile_image_url_https = StringField(required=True)
    profile_image_url = StringField(required=True)
    is_blacklisted = BooleanField(default=False)
    
    def permalink(self):
        return "%s/user/%s" % (settings.get('base_url'), self._data['username'])

class AccessToken(EmbeddedDocument):
    secret = StringField(required=True)
    user_id = IntField(required=True)
    screen_name = StringField(required=True)
    key = StringField(required=True)

class UserInfo(Document):
    meta = {
        'indexes': ['user.id_str', 'email_address', 'user.username']
    }
    user = EmbeddedDocumentField(User, required=True)
    access_token = EmbeddedDocumentField(AccessToken, required=True)
    email_address = StringField(required=False)
    role = StringField(default="user")
    last_login = DateTimeField(default=datetime.now())
    date_created = DateTimeField(default=datetime.now())
    wants_daily_email = BooleanField(default=True)
    wants_email_alerts = BooleanField(default=True)
    disqus = DictField()
    yammer = DictField()
    in_usvnetwork = BooleanField(default=False)
    tags = ListField()
    topics_following = ListField(StringField())
    
#db.user_info.ensure_index('user.screen_name')

def get_all():
    return UserInfo.objects()

def get_user_by_id_str(id_str):
    return UserInfo.objects(user__id_str=id_str).first()

def get_user_by_screen_name(screen_name):
    return UserInfo.objects(user__screen_name=screen_name).first()
    
def get_followers(topic_slug, limit=None):
    return UserInfo.objects(topics_following=topic_slug)[:limit]

def get_user_by_email(email_address):
    return UserInfo.objects(email_address=email_address).first()

def get_disqus_users():
    return UserInfo.objects(disqus__exists=true)

def get_newsletter_recipients():
    return UserInfo.objects(wants_daily_email=True)

def create_new_user(user, access_token):
    user_info_dict = {
        'user': user,
        'access_token': access_token
    }
    user_info = UserInfo(**user_info_dict)
    return user_info.save()

def get_user_count():
    return len(UserInfo.objects())

def add_tags_to_user(screen_name, tags=[]):
    # return db.user_info.update({'user.screen_name':screen_name}, {'$addToSet':{'tags':{'$each':tags}}})
    u = UserInfo.objects.get(user__screen_name=screen_name)
    for t in tags:
        if t not in u.tags:
            u.tags.append(t)
    return u
