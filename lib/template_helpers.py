from lib.sanitize import tinymce_valid_elements
import datetime
import settings
import random
    
def generate_slug(length=6):
    return ''.join(random.choice('0123456789ABCDEF') for i in range(6))

def tinymce_valid_elements_wrapper(media=True):
    return tinymce_valid_elements(media=media)

# Twitter URLs are stored as their 'normal' size
# eg. http://a0.twimg.com/profile_images/3428823565/9c49c693a9b7527b3fb7e36f6bba627f_normal.png
def twitter_avatar_size(url, size):
    if size == 'original':
        url = url.replace('_normal', '')
    else:
        url = url.replace('_normal', '_%s' % size)
    return url

# Adapted from http://bit.ly/17wpDuh
def pretty_date(d):
    diff = datetime.datetime.now() - d
    s = diff.seconds
    if diff.days != 0:
        return d.strftime('%b %d, %Y')
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{0} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{0} minutes ago'.format(s/60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{0} hours ago'.format(s/3600)

# display a permalink to a post
def post_permalink(p):
    return 'http://' + settings.get('base_url') + "/posts/" + p['slug']

def company_editlink(c):
    return "/portfolio/%s/edit" % c.get('slug','')
    #return settings.get('mongodb_edit_url_base') + "/company/" + str(c['_id'])