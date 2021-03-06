from helpers import *
import random, re, urllib, urllib2
from models import *
from geo import geotypes
from google.appengine.api import search
from google.appengine.ext import deferred
from google.appengine.ext import db, ndb
from google.appengine.api import users

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
    user = self.auth.get_user_by_session()
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
    user.reviewcount = 0
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
    if not user:
      return self.redirect("/")

    values = {
      "user": user,
    }
    render(self, 'restaurants.html', values)
    
#    ('/feed', main.Feed),
class Feed(BaseHandler):
  def get(self):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    
    feed_items = []

    for review in Review.all().order("-date_edited").fetch(20):
      try: 
        prompt = review.prompt.name
      except: 
        prompt = None
      reviewuser = User.get_by_id(int(review.userid))

      prompt = str(review.prompt.name)

      prompt = prompt.replace("{{restaurant}}", "<a style='display: inline;' href='/items/"+ str(review.item.restaurant.key().id()) +"'>"+review.item.restaurant.name+"</a>")
      prompt = prompt.replace("{{dish}}", "<a style='display: inline;' href='/vote/"+str(review.item.key().id())+"'>"+review.item.name+"</a>")

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
        "date": review.date_edited,
        "commentcount": review.commentcount if review.commentcount > 0 else 0,
      }
      feed_items.append(review)

    values = {
      "user": user,
      "feed_items": feed_items,
    }
    
    render(self, "feed.html", values)

#    ('/review/(.*)', main.ReviewPage), 
class ReviewPage(BaseHandler):
  def get(self, reviewid):
    try:
      user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    except:
      user = None
    review = Review.get_by_id(int(reviewid))

    try: 
      prompt = review.prompt.name
    except: 
      prompt = None
    reviewuser = User.get_by_id(int(review.userid))
    
    prompt = str(review.prompt.name)
    
    prompt = prompt.replace("{{restaurant}}", "<a style='display: inline;' href='/items/"+ str(review.item.restaurant.key().id()) +"'>"+review.item.restaurant.name+"</a>")
    prompt = prompt.replace("{{dish}}", "<a style='display: inline;' href='/vote/"+str(review.item.key().id())+"'>"+review.item.name+"</a>")

    if review.input:
      prompt = prompt.replace("{{input}}", "<span style='display: inline; color:red;'>"+review.input+"</span>")
      
    if review.input2:
      prompt = prompt.replace("{{input2}}", "<span type='text' name='input2' style='display: inline; color: red;'>"+review.input2+"</span>")

    comments = Comment.all().filter("review =", review).order("date_edited").run()

    commentslist = []

    for comment in comments:
      commentuser = User.get_by_id(int(comment.userid))
      commentslist.append({
        "userid" : comment.userid,
        "username" : commentuser.auth_ids[0],
        "content" : comment.content,
        "date" : comment.date_edited,
      })

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
      "date": review.date_edited,
    }

    values = {
      "user": user,
      "review": review,
      "comments": commentslist
    }      
    render(self, 'review.html', values)

  #post to /review (comment only so far)
  def post(self, reviewid):
    try:
      user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    except:
      user = None

    review = Review.get_by_id(int(reviewid))
    content = self.request.get("comment")

    comment = Comment(
      userid = user.key.id(),
      review = review,
      content = content,
    )

    try: review.commentcount += 1
    except: review.commentcount = 1
    review.put()

    comment.put()

    self.redirect("/review/"+ str(review.key().id()) )
    

#    ('/profile/(.*)/followers', main.Followers), 
class Followers(BaseHandler):
  def get(self, profileid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    profile = User.get_by_auth_id(profileid)
    if not profile:
      profile = User.get_by_id(int(profileid))
    followers = ndb.get_multi([ndb.Key(User, k) for k in profile.followers])
    values = {
      "user": user,
      "profile": profile,
      "followers": followers,
      "isfollowing": True if profileid in user.following else False,
      "profileid": profileid,
    }      
    render(self, 'followers.html', values)
    

#    ('/profile/(.*)/following', main.Following), 
class Following(BaseHandler):
  def get(self, profileid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    profile = User.get_by_auth_id(profileid)
    if not profile:
      profile = User.get_by_id(int(profileid))
    following = ndb.get_multi([ndb.Key(User, k) for k in profile.following])
    values = {
      "user": user,
      "profile": profile,
      "following": following,
      "isfollowing": True if profileid in user.following else False,
      "profileid": profileid,
    }      
    render(self, 'following.html', values)

#('/findpeople', main.FindPeople),
class FindPeople(BaseHandler):
  def get(self):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")

    values = {
      "user": user,
    }
    render(self, 'findpeople.html', values)
  def post(self):
    query = self.request.get("query")
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")

    values = {
      "user": user,
    }
    if "@" in query:
      #search emails
      result = ndb.gql("SELECT * FROM User WHERE email_address = :1", query).fetch()[0]
    else:
      #search usernames
      result = User.get_by_auth_id(query)
      
    if result:
      values["result"] = result

    values["query"] = query
    values["test"] = "HIHIHI"

    render(self, 'findpeople.html', values)    


#    ('/profile/(.*)', main.Profile), #profile?profileid
class Profile(BaseHandler):
  def get(self, profileid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    profile = User.get_by_auth_id(profileid)
    if not profile:
      profile = User.get_by_id(int(profileid))
                
    feed_items = []
    
    for review in Review.all().filter("userid =", profile.key.id()).order("-date_edited").run():
      try: 
        prompt = str(review.prompt.name)
        
      except: 
        prompt = None

      if prompt:
        prompt = prompt.replace("{{restaurant}}", "<a style='display: inline;' href='/items/"+ str(review.item.restaurant.key().id()) +"'>"+review.item.restaurant.name+"</a>")
        prompt = prompt.replace("{{dish}}", "<a style='display: inline;' href='/vote/"+str(review.item.key().id())+"'>"+review.item.name+"</a>")

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
      "isfollowing": True if profileid in user.following else False,
      "profileid": profileid,
    }      

    render(self, 'profile.html', values)

#/items/(restid)     ('/items/(.*)', main.Items), lat lng restname
class Items(BaseHandler):  
  def get(self, restaurantid = None):
    if not restaurantid:
      #get restaurant id based on name lat and long
      restaurants = getrestaurantid(self)
      restaurantid = restaurants[0]["restaurantid"]

    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    restaurant = Restaurant.get_by_id(int(restaurantid))
    values = {
      "user": user,
      "restaurant": restaurant,
      "items": restaurant.item_set,
    }      
    render(self, 'items.html', values)

#    ('/vote/(.*)', main.Vote),
class Vote(BaseHandler):
  def get(self, itemid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    item = Item.get_by_id(int(itemid))

    #getprompt and format it
    promptkey = random.choice([key for key in Prompt.all(keys_only=True).run()])
    prompt = Prompt.get(promptkey)
    
    promptname = str(prompt.name)
    promptname = promptname.replace("{{input}}", "<input type='text' name='input' style='display: inline;'>")
    promptname = promptname.replace("{{input2}}", "<input type='text' name='input2' style='display: inline;'>")
    promptname = promptname.replace("{{restaurant}}", "<span style='color: red;'>"+item.restaurant.name + "</span>")
    promptname = promptname.replace("{{dish}}", "<span style='color: red;'>"+item.name+"</span>")

    values = {
      "user": user,
      "item": item,
      "prompt": promptname,
      "promptid": prompt.key().id(),
    }      
    render(self, 'vote.html', values)

  def post(self, itemid):
    #handled via json atm
    pass


#    ('/votenew/(.*)', main.VoteNew),
class VoteNew(BaseHandler):
  def get(self, restaurantid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    restaurant = Restaurant.get_by_id(int(restaurantid))
    values = {
      "user": user,
      "restaurant": restaurant,
    }
    render(self, "votenew.html", values)

  def post(self, restaurantid):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    if not user:
      return self.redirect("/")
    restaurant = Restaurant.get_by_id(int(restaurantid))
    item = Item(
      name = self.request.get("name"),
      description = self.request.get("description"),
      price = self.request.get("price"),
      restaurant = restaurant
    )
    item.put()
    
    self.redirect("/vote/" + str(item.key().id()) )
