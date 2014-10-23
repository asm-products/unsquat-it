from mongoengine import *
import pymongo
from mongo import db
import settings
from slugify import slugify
from datetime import datetime
from lib import userdb

class Domain(Document):
  name = StringField(required=True, default="")
  user_info = ReferenceField('UserInfo')
  status = StringField(default="")
  description = StringField(default="")
  date_created = DateTimeField(default=datetime.now())

  def set_fields(self, **kwargs):
    for fname in self._fields.keys():
        if kwargs.has_key(fname):
            setattr(self, fname, kwargs[fname])
  
  def permalink(self):
    return "%s/d/%s" % (settings.get('base_url'), self._data['name'])

  def editlink(self):
  	return "%s/edit" % self.permalink()

  def unsquatitlink(self):
  	return "%s/unsquatit" % self.permalink()

def get_all():
  return Domain.objects().order_by('name')

def get_domain_by_name(name):
	return Domain.objects(name=name).first()

###########################
### ADD A NEW company
###########################
def insert_domain(domain_dict):
    new_domain = Domain(**domain_dict)
    new_domain.user = userdb.get_user_by_screen_name(self.current_user)
    new_domain.save()
    return new_domain

###########################
### UPDATE company
###########################
def update_domain(domain_dict):
    domain = get_domain_by_name(domain_dict['name'])
    domain.set_fields(**domain_dict)
    domain.user = userdb.get_user_by_screen_name('nickgrossman')
    domain.save()
    return domain