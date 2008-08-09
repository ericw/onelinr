#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp


class StartPage(webapp.RequestHandler):

  def get(self):

class ChannelPage(webapp.RequestHandler):

  def get(self):

  def post(self):


def main():
  application = webapp.WSGIApplication([('/.*', StartPage),
                                        ('/.*', ChannelPage) ],
                                       debug=False)
                                       
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
