from helpers import *
import random, re, urllib, urllib2
from models import *
from geo import geotypes
from google.appengine.api import search
from google.appengine.ext import deferred
from google.appengine.ext import db, ndb
import globs, logging

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

_ITEM_INDEX = globs._ITEM_INDEX

def something_expensive(a,b,c):
  logging.info("Doing something expensive")
  #this updates all indexes
  restaurants = Restaurant.all()
  items = Item.all()
  for r in restaurants:
    r.updateindex()
  for i in items:
    i.updateindex()

#reset everything except the user accounts
def reset_food(a,b,c):
  restaurants = Restaurant.all(keys_only=True)
  items = Item.all(keys_only=True)
  reviews = Review.all(keys_only=True)
  db.delete(restaurants)
  db.delete(items)
  db.delete(reviews)
  
######################## HANDLERS
class MainHandler(BaseHandler):
    def get(self):
        user = self.auth.get_user_by_session()
        values = {
          "user": user,
            }
        render(self, 'landing.html', values)

class SignupHandler(BaseHandler):
  def get(self):
    values = {
      "user": user,
    }
    render(self, "signup.html", values)
  def post(self):
    user_name = self.request.get('username')
    email = self.request.get('email')
    password = self.request.get('password')
    passwordtwo = self.request.get('passwordtwo')
    if password != passwordtwo:
      values = {
        "response": 0,
        "message": "Passwords do not match",
      }		
      return self.redirect("/")
      
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
      values = {
        "response": 0,
        "message": "Bad email format",
      }		
      return self.redirect("/")
        
    unique_properties = ['email_address']
    user_data = self.user_model.create_user(
      user_name,
      unique_properties,
      email_address=email,
      password_raw=password,
      verified=False, 
      admin=False,
      following=[],
      followers=[],
    )
    if not user_data[0]: #user_data is a tuple
      values = {
        "response": 0,
        "message": "Username or email already exists",
      }
      return self.redirect("/")
        
    user = user_data[1]
    user_id = user.get_id()
    user.following.append(user_id)
    user.followers.append(user_id)
    user.put()
    #token = self.user_model.create_signup_token(user_id)
    
    #verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)

    #msg = 'Send an email to user in order to verify their address. \They will be able to do so by visiting <a href="{url}">{url}</a>'

    #self.display_message(msg.format(url=verification_url))
    self.redirect('/?message=success')

class LoginHandler(BaseHandler):
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        try:
            u = self.auth.get_user_by_password(username, password, remember=True,
                                               save_session=True)
            self.redirect('/feed')
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self.redirect('/')
            
class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect('/')

#/restaurants  shows nearby restaurants
class Restaurants(BaseHandler):
  def get(self):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    urldata = {
      #"key": "AIzaSyD82p3cZfbO7xQthU1aE9Nu3L89SaEhWbI", #website
      "key": "AIzaSyBfqZNaQ6d9AtdZXPI5vkHBLk-pcq1hqOg", #server ip
      #"key": "AIzaSyCkBh8u9kR_yuyyxzeMzZDeHEyQF1PmlwU",  #personal
      "location": "",#$_GET['location'],  #lat+","+lng
      "sensor": "false",
      "types": "cafe|restaurant|bar|bakery",
      "rankby": "distance"
    }
    try:
      result = urllib2.urlopen(url + "?" + urllib.urlencode(urldata))
    except urllib2.URLError, e:
      pass

    values = {
      "user": user,
      "result": result,
    }
    render(self, 'restaurants.html', values)
    
#    ('/feed', main.Feed),
class Feed(BaseHandler):
  def get(self):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    
    feed_items = []

    for review in Review.all().order("-date_edited").run():
      try: 
        prompt = review.prompt.name
      except: 
        prompt = None
      reviewuser = User.get_by_id(int(review.userid))

      prompt = str(review.prompt.name)

      prompt = prompt.replace("{{restaurant}}", "<a style='display: inline;' href='/items?restaurantid="+ str(review.item.restaurant.key().id()) +"'>"+review.item.restaurant.name+"</a>")
      prompt = prompt.replace("{{dish}}", "<a style='display: inline;' href='/vote?restaurantid="+str(review.item.restaurant.key().id())+"&itemid="+str(review.item.key().id())+"&restaurantname="+review.item.restaurant.name+"&itemname="+review.item.name+"'>"+review.item.name+"</a>")

      if review.input:
        prompt = prompt.replace("{{input}}", "<span style='display: inline; color:red;'>"+review.input+"</span>")

      if review.input2:
        prompt = prompt.replace("{{input2}}", "<span type='text' name='input2' style='display: inline; color: red;'>"+review.input2+"</span>")

      review = {
        "username": reviewuser.auth_ids[0],
        "userid": review.userid,
        "useremail": reviewuser.email_address,
        "reviewid": review.key().id(),
        "item": review.item.name,
        "description": review.description,
        "itemid": review.item.key().id(),
        "rating": review.rating,
        "restaurant": review.item.restaurant.name,
        "restaurantid": review.item.restaurant.key().id(),
        "prompt": prompt,
      }
      feed_items.append(review)

    values = {
      "user": user,
      "feed_items": feed_items,
    }
    
    render(self, "feed.html", values)

#    ('/profile/(.*)', main.Profile), #profile?profileid
class Profile(BaseHandler):
  def get(self, profileid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    profileid = int(profileid)
    profile = User.get_by_id(profileid)
                
    feed_items = []
                
    for review in Review.all().filter("userid =", int(profileid)).order("-date_edited").run():
      try: 
        prompt = str(review.prompt.name)
        
      except: 
        prompt = None

      if prompt:
        prompt = prompt.replace("{{restaurant}}", "<a style='display: inline;' href='/items?restaurantid="+ str(review.item.restaurant.key().id()) +"'>"+review.item.restaurant.name+"</a>")
        prompt = prompt.replace("{{dish}}", "<a style='display: inline;' href='/vote?restaurantid="+str(review.item.restaurant.key().id())+"&itemid="+str(review.item.key().id())+"&restaurantname="+review.item.restaurant.name+"&itemname="+review.item.name+"'>"+review.item.name+"</a>")

        if review.input:
          prompt = prompt.replace("{{input}}", "<span style='display: inline; color:red;'>"+review.input+"</span>")

        if review.input2:
          prompt = prompt.replace("{{input2}}", "<span type='text' name='input2' style='display: inline; color: red;'>"+review.input2+"</span>")

      reviewuser = profile
      review = {
        "username": reviewuser.auth_ids[0],
        "userid": review.userid,
        "useremail": reviewuser.email_address,
        "reviewid": review.key().id(),
        "item": review.item.name,
        "description": review.description,
                                "itemid": review.item.key().id(),
        "rating": review.rating,
        "restaurant": review.item.restaurant.name,
        "restaurantid": review.item.restaurant.key().id(),
        "prompt": prompt,
      }
      feed_items.append(review)
      
    values = {
      "user": user,
      "profile": profile,
      "feed_items": feed_items,
      "followers": len(profile.followers),
      "following": len(profile.following),
      "isfollowing": True if profileid in user.following else False,
      "reviewcount": len(feed_items),
      "profileid": profileid,
    }      

    render(self, 'profile.html', values)

#/items/(restid)     ('/items/(.*)', main.Items),
class Items(BaseHandler):
  def get(self, restaurantid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    restaurant = Restaurant.get_by_id(int(restaurantid))
    values = {
      "user": user,
      "restaurant": restaurant,
    }      
    render(self, 'items.html', values)

#    ('/vote/(.*)', main.Vote),
class Vote(BaseHandler):
  def get(self, itemid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    item = Item.get_by_id(int(itemid))

    #getprompt and format it
    promptkey = random.choice([key for key in Prompt.all(keys_only=True).run()])
    prompt = Prompt.get(promptkey)
    
    promptname = str(prompt.name)
    promptname = promptname.replace("{{input}}", "<input type='text' name='input' style='display: inline;'>")
    promptname = promptname.replace("{{input2}}", "<input type='text' name='input2' style='display: inline;'>")
    promptname = promptname.replace("{{restaurant}}", "<span style='color: red;'>"+utf8_decode(restaurant)+"</span>")
    promptname = promptname.replace("{{dish}}", "<span style='color: red;'>"+item+"</span>")

    values = {
      "user": user,
      "item": item,
      "prompt": promptname,
      "promptid": prompt.key().id(),
    }      
    render(self, 'items.html', values)

  def post(self, itemid):
    #handled via json atm
    pass


