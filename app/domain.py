import app.basic
from lib import domainsdb
from slugify import slugify
import tornado.web
from lib.domainsdb import Domain
from lib import userdb

#################
### Add a domain
### /gp
#################
class NewDomain(app.basic.BaseHandler):
	@tornado.web.authenticated
	def get(self):
		domain = domainsdb.Domain()
		self.render('domain/edit_domain.html', domain=domain, mode="new")
	
	def post(self):
		domain_dict = {}
		domain_dict['name'] = self.get_argument('name', '')
		domain_dict['description'] = self.get_argument('description', '')
		domain_dict['status'] = self.get_argument('status', '')
		new_domain = Domain(**domain_dict)
		new_domain.user_info = userdb.get_user_by_screen_name(self.current_user)
		new_domain.save()
		self.set_secure_cookie('flash', 'domain added!')
		self.redirect(new_domain.permalink())

#################
### Edit a Domain
### /d/(domain)/edit
#################
class EditDomain(app.basic.BaseHandler):
	def get(self, name):
		domain = domainsdb.get_domain_by_name(name)
		self.render('domain/edit_domain.html', domain=domain, mode="edit")
	
	def post(self, name):
		domain_dict = {}
		domain_dict['name'] = self.get_argument('name', '')
		domain_dict['description'] = self.get_argument('description', '')
		domain_dict['status'] = self.get_argument('status', '')
		domain = domainsdb.update_domain(domain_dict)
		self.set_secure_cookie('flash', 'domain edited!')
		self.redirect(domain.permalink())

#################
### View a Domain
### /d/(domain)
#################
class ViewDomain(app.basic.BaseHandler):
	def get(self, name):
		domain = domainsdb.get_domain_by_name(name)
		self.render('domain/view_domain.html', domain=domain)

#################
### Unsquat a Domain!
### /d/(domain)/edit
#################
class UnsquatDomain(app.basic.BaseHandler):
	def get(self, name):
		domain = domainsdb.get_domain_by_name(name)
		self.render('domain/unsquat_it.html', domain=domain, mode="edit")
	
	def post(self, name):
		domain_dict = {}
		domain_dict['name'] = self.get_argument('name', '')
		domain_dict['description'] = self.get_argument('description', '')
		domain_dict['status'] = self.get_argument('status', '')
		domain = domainsdb.update_domain(domain_dict)
		self.set_secure_cookie('flash', 'domain edited!')
		self.redirect(domain.permalink())

##########
### All Domains
### /all
#################
class ListAll(app.basic.BaseHandler):
	def get(self):
		domains = domainsdb.get_all()
		self.render('domain/list_all.html', domains=domains)