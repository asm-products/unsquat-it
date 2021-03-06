import tornado.web
import requests
import settings
import simplejson as json
import os
import httplib
import logging
import oauth2
import time
from datetime import datetime, timedelta
from lib import userdb
from lib.postsdb import Post
import pprint
from slugify import slugify

class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self.vars = {}
        super(BaseHandler, self).__init__(*args, **kwargs)
    
    def head(self, *args, **kwargs):
        return

    def render(self, template, **kwargs):
        # add any variables we want available to all templates
        kwargs['blank_post'] = Post()
        kwargs['pprint'] = pprint
        kwargs['slugify'] = slugify
        kwargs['user_obj'] = None
        kwargs['user_obj'] = userdb.get_user_by_screen_name(self.current_user)
        kwargs['current_user_can'] = self.current_user_can
        kwargs['settings'] = settings
        kwargs['body_location_class'] = ""
        kwargs['current_path'] = self.request.uri
        kwargs['args_len'] = len(self.request.arguments)
        user_info = kwargs['user_obj']
        if self.request.path == "/":
            kwargs['body_location_class'] = "home"
        #handle flash message
        kwargs['flash_text'] = ""
        if self.get_secure_cookie('flash'):
            kwargs['show_flash'] = True
            kwargs['flash_text'] = self.get_secure_cookie('flash')
        else:
            kwargs['show_flash'] = False
        self.clear_cookie('flash')
                
        super(BaseHandler, self).render(template, **kwargs)

    def get_current_user(self):
        return self.get_secure_cookie("username")

    ''' Optional HTML body supercedes plain text body in SendGrid API'''
    def send_email(self, from_user, to_user, subject, text, html=None, from_name=None):
        if settings.get('environment') != "prod":
            logging.info("If this were prod, we would have sent email to %s" % to_user)
            return
        else:
            return requests.post(
              "https://sendgrid.com/api/mail.send.json",
              data={
                "api_user":settings.get('sendgrid_user'),
                "api_key":settings.get('sendgrid_secret'),
                "from": from_user,
                "to": to_user,
                "subject": subject,
                "text": text,
                "html": html,
                "fromname": from_name
              },
              verify=False
            )

    def is_blacklisted(self, screen_name):
        """
        Legacy Support for pre-mongoengine check.
        """
        is_blacklisted = False
        user_info = userdb.get_user_by_screen_name(screen_name)
        if user_info and user_info.user.is_blacklisted:
            is_blacklisted = True
        return is_blacklisted

    def current_user_can(self, capability):
        """
        Tests whether a user can do a certain thing.
        """
        if not self.current_user:
            return False
        result = False        
        u = userdb.get_user_by_screen_name(self.current_user)
        if u and u.role:
            if capability in settings.get('%s_capabilities' % u.role):
                result = True
            else:
                result = False
        return result

    def api_response(self, data):
        # return an api response in the proper output format with status_code == 200
        self.write_api_response(data, 200, "OK")

    def error(self, status_code, status_txt, data=None):
        # return an api error in the proper output format
        self.write_api_response(status_code=status_code, status_txt=status_txt, data=data)

    def write_api_response(self, data, status_code, status_txt):
        # return an api error based on the appropriate request format (ie: json)
        format = self.get_argument('format', 'json')
        callback = self.get_argument('callback', None)
        if format not in ["json"]:
            status_code = 500
            status_txt = "INVALID_ARG_FORMAT"
            data = None
            format = "json"
        response = {'status_code':status_code, 'status_txt':status_txt, 'data':data}

        if format == "json":
            data = json.dumps(response)
            if callback:
                self.set_header("Content-Type", "application/javascript; charset=utf-8")
                self.write('%s(%s)' % (callback, data))
            else:
                self.set_header("Content-Type", "application/json; charset=utf-8")
                self.write(data)
            self.finish()

    def write_error(self, status_code, **kwargs):
        self.require_setting("static_path")
        if status_code in [404, 500, 503, 403, 405]:
            filename = os.path.join(self.settings['static_path'], '%d.html' % status_code)
            if os.path.exists(filename):
                f = open(filename, 'r')
                data = f.read()
                f.close()
                return self.write(data)
        return self.write("<html><title>%(code)d: %(message)s</title>" \
                "<body class='bodyErrorPage'>%(code)d: %(message)s</body></html>" % {
            "code": status_code,
            "message": httplib.responses[status_code],
        })
