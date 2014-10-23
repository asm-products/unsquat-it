import app.basic
from lib import domainsdb
from slugify import slugify

#############
### HOME
### /about
#############
class Home(app.basic.BaseHandler):
    def get(self):
        domains = domainsdb.get_all()
        return self.render('general/home.html', domains=domains)

#############
### ABOUT
### /about
#############
class About(app.basic.BaseHandler):
    def get(self):
        return self.write('about!')