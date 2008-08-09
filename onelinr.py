#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import db

from google.appengine.ext import webapp
from google.appengine.ext.webapp \
  import template

from django.utils import simplejson
  
from google.appengine.ext.webapp.util import run_wsgi_app

class Channel(db.Model):
  name = db.StringProperty(required=True)
  fore_color = db.StringProperty()
  back_color = db.StringProperty()
  font = db.TextProperty()
  date_created = db.DateTimeProperty(auto_now_add=True)

class Post(db.Model):
  text = db.StringProperty()
  belongs_to = db.ReferenceProperty(Channel)
  date_posted = db.DateTimeProperty(auto_now_add=True)
  post_id = db.IntegerProperty()
  
class StartPage(webapp.RequestHandler):

  def get(self):
    channels = Channel.all()
    self.response.out.write(template.render('index.html', {'channels':channels}))

class AboutPage(webapp.RequestHandler):

  def get(self):
    self.response.out.write(template.render('about.html', {}))

class ChannelPage(webapp.RequestHandler):

  def get(self):
    name = url_to_channel_name(self.request.uri)
    
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)      
    channel = q.get()

    if not channel:
      channel = Channel(name=name)
      channel.put()
    
    posts = Post.all()
    posts.filter("belongs_to =", channel.key())    
    
    self.response.out.write(template.render('channel.html', {'channel':channel, 'posts':posts}))

  def post(self):
    channel_key = self.request.get('key')
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :channel_key ORDER BY post_id DESC", channel_key=channel_key)      
    last_post = q.get()
    
    if last_post:
      next_id = last_post.post_id+1
    else: 
      next_id = 1
    
    post = Post(text=self.request.get('value'), belongs_to=db.get(channel_key), post_id=next_id)
    post = db.get(post.put())
    self.response.out.write("{'post_id':"+str(post.post_id)+",'text':'"+post.text+"'}")
    

class LatestPosts(webapp.RequestHandler):
  def get(self):
    name = url_to_channel_name(self.request.uri)
    get_from = self.request.get('from_id')
    
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)      
    channel = q.get()
    
    # ADD ERROR CHECKING
    
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :key AND post_id > :get_from", key=channel.key(), get_from=get_from)   #MAKE THIS BETTER   
    posts = q.fetch(100) 
    
    self.response.out.write(simplejson.dumps(posts))

def main():
  application = webapp.WSGIApplication([('/', StartPage),
                                        ('/about', AboutPage),
                                        ('/.*/latest', LatestPosts),
                                        ('/.*', ChannelPage) ],
                                       debug=True)
                                       
  run_wsgi_app(application)


def url_to_channel_name(url):
  url_array = url.split("/")
  if len(url_array) > 3:
    return url_array[3].lower()
  else:
    return ""

if __name__ == '__main__':
  main()
