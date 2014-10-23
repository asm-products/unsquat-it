import os
import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.web

import logging

# settings is required/used to set our environment
import settings

import app.user
import app.domain
import app.basic
import app.twitter
import app.general

import templates

if settings.get('environment') == "prod":
  import newrelic.agent
  path = os.path.join(settings.get("project_root"), 'newrelic.ini')
  newrelic.agent.initialize(path, settings.get("environment"))

class Application(tornado.web.Application):
    def __init__(self):

        debug = (settings.get('environment') == "dev")

        app_settings = {
          "cookie_secret" : settings.get('cookie_secret'),
          "login_url": "/auth/twitter",
          "debug": debug,
          "static_path" : os.path.join(os.path.dirname(__file__), "static"),
          "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
        }

        handlers = [
          # account stuff
          (r"/auth/email/?", app.user.EmailSettings),
          (r"/auth/logout/?", app.user.LogOut),
          (r"/user/(?P<username>[A-z-+0-9]+)/settings/?", app.user.UserSettings),
          (r"/user/settings?", app.user.UserSettings),
          (r"/user/(?P<screen_name>[A-z-+0-9]+)", app.user.Profile),
          (r"/user/(?P<screen_name>[A-z-+0-9]+)/(?P<section>[A-z]+)", app.user.Profile),
          (r"/auth/twitter/?", app.twitter.Auth),
          (r"/twitter", app.twitter.Twitter),
          
          # domain stuff
          (r"/go$", app.domain.NewDomain),
          (r"/d/(?P<name>[A-z-.+0-9]+)$", app.domain.ViewDomain),
          (r"/d/(?P<name>[A-z-.+0-9]+)/edit", app.domain.EditDomain),
          (r"/d/(?P<name>[A-z-.+0-9]+)/unsquatit", app.domain.UnsquatDomain),

          (r'/$', app.general.Home),
        ]

        tornado.web.Application.__init__(self, handlers, **app_settings)

def main():
    tornado.options.define("port", default=8001, help="Listen on port", type=int)
    tornado.options.parse_command_line()
    logging.info("starting tornado_server on 0.0.0.0:%d" % tornado.options.options.port)
    http_server = tornado.httpserver.HTTPServer(request_callback=Application(), xheaders=True)
    http_server.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
