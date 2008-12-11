#!/usr/bin/env python

import wsgiref.handlers
import logging
from google.appengine.ext import db

from google.appengine.ext import webapp
from google.appengine.ext.webapp \
  import template
  
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from django.conf import settings
import textile

from google.appengine.api import memcache

from django.utils import simplejson

settings.INSTALLED_APPS = ('django.contrib.markup', 'onelinr')

SKIP_LIST = ["favicon.ico","robots.txt", "feed"]

class Channel(db.Model):
  name = db.StringProperty(required=True)
  post_count = db.IntegerProperty(default=0)
  fore_color = db.StringProperty()
  back_color = db.StringProperty()
  font = db.TextProperty()
  date_created = db.DateTimeProperty(auto_now_add=True)

class User(db.Model):
  google_user = db.UserProperty(required=True)
  handle = db.StringProperty(required=True)

class Post(db.Model):
  text = db.StringProperty()
  belongs_to = db.ReferenceProperty(Channel)
  date_posted = db.DateTimeProperty(auto_now_add=True)
  post_id = db.IntegerProperty()
  posted_by = db.ReferenceProperty(User)
    
class StartPage(webapp.RequestHandler):

  def get(self):
    channelCloud = memcache.get("channelCloud")
    if channelCloud is None:    
      channels = Channel.all()
      channels.filter("post_count >", 0)
      channels.order("-post_count")
      channelCloud = renderChannelCloud(channels);
      memcache.set("channelCloud", channelCloud, 86400)
    
    self.response.out.write(template.render('index.html', {'channelCloud':channelCloud,'page_title':'Onelinr'}))

class ChannelPage(webapp.RequestHandler):

  def get(self):
    name = url_to_channel_name(self.request.uri)
    
    if name in SKIP_LIST:
      self.redirect("/")
      return
    
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)      
    channel = q.get()

    if not channel:
      channel = Channel(name=name)
      channel.put()
    
    posts = Post.all()
    posts.filter("belongs_to =", channel.key()).order('-post_id')
    
    google_user = users.get_current_user()
    user = get_user(google_user)
    
    user_html = generate_handle_links(google_user, user, self.request)
    
    self.response.out.write(template.render('channel.html', {'channel':channel, 'posts':posts, 'user_html':user_html,'page_title':'Onelinr Channel: ' + channel.name}))

  def post(self):
    google_user = users.get_current_user()
    user = get_user(google_user)

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
    
    if google_user and user:
      post.posted_by = user
      handle = user.handle
    else:
      handle = ""

    channel.post_count += 1
    
    batch = [post, channel]
    db.put(batch)
    
    d = {
      'post_id':post.post_id,
      'text':textile.textile(post.text),
      'handle':handle,
    }

    self.response.out.write(simplejson.dumps(d))

class HandlePage(webapp.RequestHandler):

  def get(self):
    channel_name = url_to_channel_name(self.request.uri)
    google_user = users.get_current_user()

    if not google_user:
      self.redirect(users.create_login_url(self.request.uri))
    
    if get_user(google_user) and self.request.get("c") != "1":
      self.redirect("/"+channel_name)
    elif get_user(google_user) and self.request.get("c") == "1":
      user = get_user(google_user)
      logging.info(user.handle)
      self.response.out.write(template.render('handle.html',{'page_title':'Onelinr','channel':channel_name,'handle':user.handle}))
    else:
      self.response.out.write(template.render('handle.html',{'page_title':'Onelinr','channel':channel_name}))

  def post(self):
    channel_name = url_to_channel_name(self.request.uri)
    
    self.request.get("handle")
    
    handle = self.request.get("handle").strip()
        
    if len(handle) < 1:
      self.redirect(self.request.uri)
    else:
      google_user = users.get_current_user()
    
      if not google_user:
        self.redirect(user.get_login_url(self.request.uri))      
    
      user = get_user(google_user)
    
      if not user:
        user = User(handle=handle, google_user=google_user)
      else:
        user.handle = handle
    
      user.put()
    
      self.redirect("/"+channel_name)

class ChannelFeed(webapp.RequestHandler):
  def get(self):
    name = url_to_channel_name(self.request.uri)
    q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)      
    channel = q.get()

    if not channel:
      channel = Channel(name=name)
      channel.put()
    
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :channel ORDER BY post_id DESC", channel=channel)   
    posts = q.fetch(20) #20 latest is sufficient
    
    self.response.out.write(template.render('channel_feed.html', {'channel':channel, 'posts':posts}))

class Feed(webapp.RequestHandler):
  def get(self):

    q = db.GqlQuery("SELECT * FROM Post ORDER BY date_posted DESC")   
    posts = q.fetch(20) #20 latest is sufficient
    
    self.response.out.write(template.render('feed.html', {'posts':posts}))
    
class LatestPosts(webapp.RequestHandler):
  def get(self):
    name = url_to_channel_name(self.request.uri)
    get_from = self.request.get('from_id')
    
    channel = memcache.get(name)
    if channel is None:
      q = db.GqlQuery("SELECT * FROM Channel WHERE name = :name", name=name)
      channel = q.get()
      memcache.set(name, channel)
    
    q = db.GqlQuery("SELECT * FROM Post WHERE belongs_to = :channel AND post_id > :get_from ORDER BY post_id DESC", channel=channel, get_from=int(get_from))   
    posts = q.fetch(50)
    
    d = {}    
    for post in posts:
      if post.posted_by:
        handle = post.posted_by.handle
      else:
        handle = ""

      d.update({
        'post_id':post.post_id,
        'text':textile.textile(post.text),
        'handle':handle,
      })
    
    if len(d) > 0:  
      tmp = [d]
      self.response.out.write(simplejson.dumps(tmp))
    else:
      self.response.out.write("[]")
      
def main():
  application = webapp.WSGIApplication([('/', StartPage),
                                        ('/.*/handle', HandlePage),
                                        ('/feed', Feed),
                                        ('/feed/', Feed),
                                        ('/.*/feed', ChannelFeed),
                                        ('/.*/feed/', ChannelFeed),
                                        ('/.*/latest', LatestPosts),
                                        ('/.*', ChannelPage) ],
                                       debug=False)

  run_wsgi_app(application)

# display channel tag cloud
def renderChannelCloud(channels):
  max, min = 0, 0
  classes = ["size1","size2","size3","size4","size5"]

  for c in channels:
    if c.post_count > max:
      max = c.post_count
    if c.post_count < min:
      min = c.post_count

  divisor = ((max - min) / len(classes)) + 1

  channelList = ""
  for c in channels:
    channelList += "<li class='" + classes[(c.post_count - min) / divisor] + "'><a href='/" + c.name + "'>" + c.name + "</a></li>"

  return channelList

def get_user(google_user):
  q = db.GqlQuery("SELECT * FROM User WHERE google_user = :google_user", google_user=google_user)  
  return q.get()

def generate_handle_links(google_user, user, request):
  channel_name = url_to_channel_name(request.uri)
  if google_user:
    if user:
      url = users.create_logout_url(request.uri)
      html = "<span class='user'>Your handle is <em>"+user.handle+"</em>, <a href='/"+channel_name+"/handle?c=1'>change it</a> or <a href='"+url+"'>Sign out</a></span>"
    else:
      url = users.create_logout_url(request.uri)
      html = "<span class='user'><a href='/"+channel_name+"/handle'>Choose a handle</a> or <a href='"+url+"'>Sign out</a></span>"
  else:
    url = users.create_login_url("/"+channel_name+"/handle")
    html = "<span class='user'><a href='"+url+"'>Sign in</a></span>"
  
  return html

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
