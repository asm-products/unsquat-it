#-*- coding:utf-8 -*-
import app.basic

import logging
import re
import settings
import tornado.web
import tornado.options
import urllib
from customerio import CustomerIO
import datetime
import time
from urlparse import urlparse
from lib import bitly
from lib import google
from lib import mentionsdb
from lib import postsdb
from lib import sanitize
from lib import tagsdb
from lib import userdb
from lib import disqus
from lib import commentsdb
from lib import template_helpers
from lib.postsdb import Post
from lib.userdb import User

cio = CustomerIO(settings.get('customer_io_site_id'), settings.get('customer_io_api_key'))

###############
### View Comment
### /comments/([^\/]+)       (GET)
###/comments/([^\/]+)/reply  (POST)
###############
class ViewComment(app.basic.BaseHandler):
	def get(self, comment_slug):
		return self.write('ViewComment GET')
	
	def post(self):
		return self.write('ViewComment POST')


###############
### Add Comment
### /posts/([^\/]+)/add_comment
###############
class AddComment(app.basic.BaseHandler):
	def get(self):
		return self.write('get')

	def post(self, post_slug):
		post = postsdb.get_post_by_slug(post_slug)
		post_owner = userdb.get_user_by_screen_name(post.user.screen_name)
		user_info = userdb.get_user_by_screen_name(self.current_user)
		firebase_id = self.get_argument('firebase_id', None)
		parent_comment = None
		if self.get_argument('parent_comment_id', '') != "":
			parent_comment = commentsdb.get_comment_by_id(self.get_argument('parent_comment_id', ''))
		comment = commentsdb.add_comment(post, user_info, self.get_argument('comment_body_text', ''), parent_comment, firebase_id)
		if comment.status == "published":						            
			#self.set_secure_cookie("flash", "Comment added!")
			#self.redirect(post.permalink())
			self.write('success')
		else:
			self.write('error')