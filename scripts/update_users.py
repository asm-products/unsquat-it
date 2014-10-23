# Run by Heroku scheduler every night
# If running locally, uncomment below imports
import sys
try:
	sys.path.insert(0, '/Users/nick/dev/usv/usv.com')
except:
	print "could not insert path"
import settings
import tweepy
import urllib2
from datetime import datetime
from lib import userdb
from lib import postsdb

###########################
### SCRIPT FUNCTIONS
###########################
''' Updates twitter account of id id_str, or else updates all twitter accounts.
	Updating all accounts will probably cause API to puke from too many requests '''
def update_twitter(id_str=None, api=None):
	if not api:
		consumer_key = settings.get('twitter_consumer_key')
		consumer_secret = settings.get('twitter_consumer_secret')
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret, secure=True)
		api = tweepy.API(auth)

	if id_str:
		users = [userdb.get_user_by_id_str(id_str)]
	else:
		users = userdb.get_all()

	for u in users:
		id_str = u.user.id_str
		twitter_user = api.get_user(id=id_str)
		if id_str != twitter_user.id_str:
			raise Exception

		# Update UserInfo.user with new data from Twitter
		u.user.auth_type = 'twitter'
		u.user.id_str = twitter_user.id_str
		u.user.username = twitter_user.screen_name
		u.user.fullname = twitter_user.name
		u.user.screen_name = twitter_user.screen_name
		u.user.profile_image_url = twitter_user.profile_image_url
		u.user.profile_image_url_https = twitter_user.profile_image_url_https
		u.save()

		print "++ Updated user @%s" % u.user.username
		user_posts = postsdb.get_posts_by_screen_name(twitter_user.screen_name, per_page=100, page=1)
		for p in user_posts:
			p.user = u.user
			p.save()
			print "++++ Updated %s info for %s" % (p.user.screen_name, p.title)

''' Only updates a user if their twitter profile image URL returns a 404 '''
def update_twitter_profile_images(username="all"):
	consumer_key = settings.get('twitter_consumer_key')
	consumer_secret = settings.get('twitter_consumer_secret')
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret, secure=True)
	api = tweepy.API(auth)
	if username == "all":
	  for user in userdb.get_all():
		  print "Checking user %s" % user['user']['screen_name']
		  try:
			  response= urllib2.urlopen(user['user']['profile_image_url_https'])
		  except urllib2.HTTPError, e:
			  if e.code == 404:
				  update_twitter(id_str=user['user']['id_str'], api=api)
	else:
	  user = userdb.get_user_by_screen_name(username)
	  print "Checking user %s" % user['user']['screen_name']
	  try:
		  response= urllib2.urlopen(user['user']['profile_image_url_https'])
	  except urllib2.HTTPError, e:
		  if e.code == 404:
			  update_twitter(id_str=user['user']['id_str'], api=api)
			  
			  
			  
update_twitter_profile_images()
			  
			  
			  
			  