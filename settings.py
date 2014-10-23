import os
import time
import tornado.options

# Environmenal settings for heroku#
# If you are developing for heroku and want to set your settings as environmental vars
# create settings_local_environ.py in the root folder and use:
# os.environ['KEY'] = 'value'
# to simulate using heroku config vars
# this is better than using a .env file and foreman
# since it still allows you to see logging.info() output.
# Make sure to also put import os in this settings_local_environ.py


try:
    import settings_local_environ
except:
    pass

time.tzset()

tornado.options.define("environment", default="dev", help="environment")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))

options = {
  'dev' : {
    'mongo_database' : {'host' : os.environ.get('MONGODB_URL'), 'port' : 27017, 'db' : os.environ.get('DB_NAME')},
    'base_url' : os.environ.get('BASE_URL'),
  },
  'test' : {
    'mongo_database' : {'host' : os.environ.get('MONGODB_URL'), 'port' : 27017, 'db' : os.environ.get('DB_NAME')},
    'base_url' : os.environ.get('BASE_URL'),
  },
  'prod' : {
    'mongo_database' : {'host' : os.environ.get('MONGODB_URL'), 'port' : 27017, 'db' : os.environ.get('DB_NAME')},
    'base_url' : os.environ.get('BASE_URL'),
  },
}

default_options = {
  'base_url': os.environ.get("BASE_URL"),

  'project_root': os.path.abspath(os.path.join(os.path.dirname(__file__))),

  # twiter details
  'twitter_consumer_key' : '',
  'twitter_consumer_secret' : '',

  # sendgrid details
  'sendgrid_user': os.environ.get("SENDGRID_USER"),
  'sendgrid_secret': os.environ.get("SENDGRID_SECRET"),

  # google api key
  'google_api_key': os.environ.get("GOOGLE_API_KEY"),

  # customer io
  'customer_io_site_id': os.environ.get("CUSTOMER_IO_SITE_ID"),
  'customer_io_api_key': os.environ.get("CUSTOMER_IO_API_KEY"),

  # other control variables
  'tinymce_valid_elements': '',
  'post_char_limit': 1000,
  'sticky': None,
  'read_only' : False,
  'max_simultaneous_connections' : 10,
  'hot_post_set_count': 200,

### DELETE STAFF[]
  'staff':[
    "nickgrossman",
    "natematias"
  ],

  # define the various roles and what capabilities they support
  'staff_capabilities': [
    'see_admin_link',
    'delete_users',
    'delete_posts',
    'post_rich_media',
    'feature_posts',
    'edit_posts',
    'super_upvote',
    'super_downvote',
    'downvote_posts',
    'manage_comments',
    'view_post_sort_score',
  ],
  'user_capabilities': [],

  'module_dir': os.path.join(PROJECT_ROOT, 'templates/modules')
}

def get(key):
    # check for an environmental variable (used w Heroku) first
    if os.environ.get('ENVIRONMENT'):
        env = os.environ.get('ENVIRONMENT')
    else:
        env = tornado.options.options.environment

    if env not in options:
        raise Exception("Invalid Environment (%s)" % env)

    if key == 'environment':
        return env

    v = options.get(env).get(key) or os.environ.get(key.upper()) or default_options.get(key)

    if callable(v):
        return v

    if v is not None:
        return v

    return default_options.get(key)
