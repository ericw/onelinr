#!/usr/bin/env python

import wsgiref.handlers
import logging
from google.appengine.ext import db

from google.appengine.ext import webapp
from google.appengine.ext.webapp \
  import template
  
import re  
from google.appengine.ext.webapp.util import run_wsgi_app
from django.conf import settings
import textile

settings.INSTALLED_APPS = ('django.contrib.markup', 'onelinr')

SKIP_LIST = ["favicon.ico","robots.txt"]

class Channel(db.Model):
  name = db.StringProperty(required=True)
  post_count = db.IntegerProperty(0)
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
    channels.order("-post_count")
    self.response.out.write(template.render('index.html', {'channels':channels}))

class ChannelPage(webapp.RequestHandler):

  def get(self):
    name = url_to_channel_name(self.request.uri)
    
    if name in SKIP_LIST:
      self.redirect("/")
      return
    
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)      
    channel = q.get()

    if not channel:
      channel = Channel(name=name,post_count=0)
      channel.put()
    
    posts = Post.all()
    posts.filter("belongs_to =", channel.key()).order('-post_id')
    
    self.response.out.write(template.render('channel.html', {'channel':channel, 'posts':posts}))

  def post(self):
    channel_key = self.request.get('key')
    channel = db.get(channel_key)
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :channel ORDER BY post_id DESC", channel=channel)

    last_post = q.get()
    
    if last_post:
      next_id = last_post.post_id+1
    else: 
      next_id = 1    
    
    # force_unicode function from django used here
    post = Post(text=force_unicode(self.request.get('value')), belongs_to=channel, post_id=next_id)
    post = db.get(post.put())

    # update post_count
    if post:
      channel = db.get(channel_key)
      logging.info(channel.post_count)
      channel.post_count = channel.post_count + 1
      channel.put()
      
    self.response.out.write("{'post_id':"+str(post.post_id)+",'text':'"+re.escape(textile.textile(post.text))+"'}")

class ChannelFeed(webapp.RequestHandler):
  def get(self):
    name = url_to_channel_name(self.request.uri)
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)      
    channel = q.get()

    if not channel:
      channel = Channel(name=name)
      channel.put()
    
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :channel ORDER BY post_id DESC", channel=channel)   
    posts = q.fetch(100) #100 latest is sufficient
    
    self.response.out.write(template.render('channel_feed.html', {'channel':channel, 'posts':posts}))


class Feed(webapp.RequestHandler):
  def get(self):

    q = db.GqlQuery("SELECT * FROM Post ORDER BY date_posted DESC")   
    posts = q.fetch(100) #100 latest is sufficient
    
    self.response.out.write(template.render('feed.html', {'posts':posts}))
    
class LatestPosts(webapp.RequestHandler):
  def get(self):
    name = url_to_channel_name(self.request.uri)
    get_from = self.request.get('from_id')
    
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)
    channel = q.get()
    
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :channel AND post_id > :get_from ORDER BY post_id DESC", channel=channel, get_from=int(get_from))   
    posts = q.fetch(100)
    
    # Own JSON formatting
    posts_json = "["
    idx = 1
    for post in posts:
      posts_json += "{'post_id':"+str(post.post_id)+",'text':'"+re.escape(textile.textile(post.text))+"'}"
      if idx != len(posts):
        posts_json += ","
      idx += 1
    posts_json += "]"
        
    self.response.out.write(posts_json)

def main():
  application = webapp.WSGIApplication([('/', StartPage),
                                        ('/feed', Feed),
                                        ('/.*/feed', ChannelFeed),
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

#from http://code.djangoproject.com/browser/django/trunk/django/utils/encoding.py
def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_unicode, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int, long, datetime.datetime, datetime.date, datetime.time, float)):
        return s
    try:
        if not isinstance(s, basestring,):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), encoding, errors)
        elif not isinstance(s, unicode):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError, e:
        raise DjangoUnicodeDecodeError(s, *e.args)
    return s

def utf8string(s):
  return unicode(s, 'utf-8') 

if __name__ == '__main__':
  main()
