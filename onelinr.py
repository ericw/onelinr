#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import db

from google.appengine.ext import webapp
from google.appengine.ext.webapp \
  import template
  
from google.appengine.ext.webapp.util import run_wsgi_app

class StartPage(webapp.RequestHandler):

  def get(self):
    self.response.out.write(template.render('index.html', {}))

class AboutPage(webapp.RequestHandler):

  def get(self):
    self.response.out.write(template.render('about.html', {}))

class ChannelPage(webapp.RequestHandler):

  def get(self):
    self.response.out.write(template.render('channel.html', {}))

  def post(self):
    self.response.out.write("Ajax")
    

def main():
  application = webapp.WSGIApplication([('/', StartPage),
                                        ('/about', AboutPage),
                                        ('/.*', ChannelPage) ],
                                       debug=True)
                                       
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
