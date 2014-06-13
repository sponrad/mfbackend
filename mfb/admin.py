from helpers import *
import helpers
import random
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
class SignupHandler(BaseHandler):
  def post(self):
    user_name = self.request.get('username')
    email = self.request.get('email')
    name = self.request.get('name')
    password = self.request.get('password')
    last_name = self.request.get('lastname')

    unique_properties = ['email_address']
    user_data = self.user_model.create_user(user_name,
      unique_properties,
      email_address=email, name=name, password_raw=password,
      last_name=last_name, verified=False, admin=False)
    if not user_data[0]: #user_data is a tuple
      self.display_message('Unable to create user for email %s because of \        duplicate keys %s' % (user_name, user_data[1]))
      return
    
    user = user_data[1]
    user_id = user.get_id()
    user.put()
    #token = self.user_model.create_signup_token(user_id)

    #verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)

      #msg = 'Send an email to user in order to verify their address. \They will be able to do so by visiting <a href="{url}">{url}</a>'

    #self.display_message(msg.format(url=verification_url))
    self.redirect(self.uri_for('home'))

class LoginHandler(BaseHandler):
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        try:
            u = self.auth.get_user_by_password(username, password, remember=True,
                                               save_session=True)
            self.redirect(self.uri_for('home'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self.redirect(self.uri_for('home'))
            
class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect(self.uri_for('home'))

class MainHandler(BaseHandler):
    def get(self):
        user = self.auth.get_user_by_session()
        values = {
            }
        render(self, 'admin/home.html', values)

class Password(BaseHandler):
  def get(self):
    user = self.auth.get_user_by_session()
    message = self.request.get("m")
    values = {
      "message": message if message else None
      }
    render(self, 'admin/password.html', values)
  def post(self):
    username = self.request.get("username")
    rawpassword = self.request.get("password")
    rawpasswordcheck = self.request.get("password2")
    if not rawpassword == rawpasswordcheck:
      return self.redirect("/_a/password")
    user = User.get_by_auth_id(username)
    user.password = security.generate_password_hash(rawpassword)
    user.put()
    self.redirect("/_a/password?m=done")


class Restaurants(BaseHandler):
    @admin_required
    def get(self):
        restaurants = Restaurant.all().run()
        values = {
            "restaurants": restaurants,
            }
        render(self, "admin/restaurants.html", values)
    @admin_required
    def post(self):
        restaurant = Restaurant(
            name = self.request.get("name"),
            numberofitems = 0
            )
        restaurant.put()
        helpers.createrestaurantdocument(restaurant)
        self.redirect('/_a/restaurant/' + str(restaurant.key().id()))

class RestaurantPage(BaseHandler):
    @admin_required
    def get(self, restaurantid):
      restaurant = Restaurant.get_by_id(int(restaurantid))
      values = {
        "restaurant": restaurant,
        }
      render(self, "admin/restaurant.html", values)
    @admin_required
    def post(self, restaurantid):      
      restaurant = Restaurant.get_by_id(int(restaurantid))
      if self.request.get("action") == "additem":
        item = Item(
          name = self.request.get("name"),
          description = self.request.get("description"),
          price = self.request.get("price"),
          restaurant = restaurant,          
          )
        item.put()
        restaurant.numberofitems += 1
        restaurant.put()
        doc = helpers.createitemdocument(item, restaurant)
      self.redirect('/_a/restaurant/' + str(restaurant.key().id()))

class Cards(BaseHandler):
  @admin_required
  def get(self):
    cards = Card.all().run()
    values = {
      "cards": cards,
      }
    render(self, 'admin/cards.html', values)
  def post(self):
    if self.request.get("action") == "addcard":
      try:
        ratingvalue = int(self.request.get("ratingvalue"))
      except:
        ratingvalue = 50
      card = Card(
        name = self.request.get("name"),
        ratingvalue = ratingvalue
        )
      card.put()
      self.redirect("/_a/cards")

class Prompts(BaseHandler):
  @admin_required
  def get(self):
    prompts = Prompt.all().run()
    values = {
      "prompts": prompts,
      }
    render(self, 'admin/prompts.html', values)
  def post(self):
    if self.request.get("action") == "addprompt":
      prompt = Prompt(
        name = self.request.get("name")
        )
      prompt.put()
      self.redirect("/_a/prompts")

class CardHand(BaseHandler):
  @admin_required
  def get(self):
    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
    try: user.cardhand
    except: 
      user.cardhand = [0]
      user.put()
    try:
      hand = [Card.get(key) for key in user.cardhand]
    except:
      hand = []
    values = {
      "user": user,
      "hand": hand,
      }
    render(self, 'admin/hand.html', values)
  def post(self):
    if self.request.get("action") == "mulligan":
      user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))
      #redraw all the cards in the hand
      #lets say a hand is 2 good cards, 2 bad cards and 2 meh cards
      goodcards = Card.all(keys_only=True).filter('ratingvalue =', 100).fetch(2000)
      mehcards = Card.all(keys_only=True).filter('ratingvalue =', 50).fetch(2000)
      badcards = Card.all(keys_only=True).filter('ratingvalue =', 0).fetch(2000)
      hand = [
        str(random.choice(goodcards)),
        str(random.choice(goodcards)),
        str(random.choice(mehcards)),
        str(random.choice(mehcards)),
        str(random.choice(badcards)),
        str(random.choice(badcards)),
        ]
      random.shuffle(hand)
      user.cardhand = hand
      user.put()
      self.redirect("/_a/hand")

class ItemVote(BaseHandler):
  def get(self):
    itemkey = random.choice([key for key in Item.all(keys_only=True).run()])
    item = Item.get(itemkey)

    promptkey = random.choice([key for key in Prompt.all(keys_only=True).run()])
    prompt = Prompt.get(promptkey)

    cardkeys = [key for key in Card.all(keys_only=True).run()]
    random.shuffle(cardkeys)
    cards = Card.get(cardkeys[:6])

    user = User.get_by_id(int(self.auth.get_user_by_session()['user_id']))

    '''
    try: user.cardhand
    except: 
      user.cardhand = [0]
      user.put()
    try:
      hand = [Card.get(key) for key in user.cardhand]
    except:
      hand = []
      '''

    values = {
      "user": user,
      "item": item,
      "prompt": prompt,
      #"hand": hand,
      "hand": cards,
      }
    render(self, 'admin/itemvote.html', values)
  def post(self):
    pass
        
class Editable(BaseHandler):
  @admin_required
  def get(self):
    self.response.out.write("there you are")
  @admin_required
  def post(self):
    id, action = self.request.get('id').split(".")
    value = self.request.get('value')
    if action == "restaurant_name":
      restaurant = Restaurant.get_by_id(int(id))
      restaurant.name = value
      restaurant.put()
      restaurant.updateindex()
      for item in restaurant.item_set:
        item.updateindex()
      self.response.out.write(value)
    if action ==  "restaurant_address":
      #set the location, recalc the geohash
      location = Restaurant.get_by_id(int(id))
      location.address = value.split(",").replace(" ", "")[0]
      location.city = value.split(",").replace(" ", "")[1]
      location.zipcode = value.split(",").replace(" ", "")[2]
      location.updatelocation()
      location.put()
      location.restaurant.put()
      restaurant.updateindex()
      for item in restaurant.item_set:
        item.updateindex()
      self.response.out.write(value)
    if action == "item_name":
      item = Item.get_by_id(int(id))
      item.name = value
      item.put()
      item.restaurant.put()
      item.updateindex()
      self.response.out.write(value)
    if action == "item_description":
      item = Item.get_by_id(int(id))
      item.description = value
      item.put()
      item.restaurant.put()
      item.updateindex()
      self.response.out.write(value)
    if action == "item_price":
      item = Item.get_by_id(int(id))
      item.price = value
      item.put()
      item.restaurant.put()
      item.updateindex()
      self.response.out.write(value)
    if action == "card_name":
      card = Card.get_by_id(int(id))
      card.name = value
      card.put()
      self.response.out.write(value)
    if action == "card_ratingvalue":
      card = Card.get_by_id(int(id))
      card.ratingvalue = int(value)
      card.put()
      self.response.out.write(value)
    if action == "prompt_name":
      prompt = Prompt.get_by_id(int(id))
      prompt.name = value
      prompt.put()
      self.response.out.write(value)

class AjaxHandler(BaseHandler):
  @admin_required
  def post(self):
    action = self.request.get("action")
    if action == "complete_check":
      restaurantid = self.request.get("restaurantid")
      restaurant = Restaurant.get_by_id(int(restaurantid))
      restaurant.completecheck = True if not restaurant.completecheck else False
      restaurant.put()
      value = "true" if restaurant.completecheck else "false"
    self.response.out.write(value)

class Delete(BaseHandler):
  @admin_required
  def get(self):
    action = self.request.get("action")
    id = self.request.get("id")
    if action == "restaurant":
      restaurant = Restaurant.get_by_id(int(id))
      restaurant.delete()
      self.redirect("/_a/restaurants")
    if action == "item":
      item = Item.get_by_id(int(id))
      restaurant = item.restaurant
      item.delete()
      restaurant.numberofitems -= 1
      restaurant.put()
      self.redirect("/_a/restaurant/" + str(restaurant.key().id()))
    if action == "card":
      card = Card.get_by_id(int(id))
      card.delete()
      self.redirect("/_a/cards")
    if action == "prompt":
      prompt = Prompt.get_by_id(int(id))
      prompt.delete()
      self.redirect("/_a/prompts")

class Maintain(BaseHandler):
  @admin_required
  def get(self):
    action = self.request.get("action")
    if action == "":
      return self.response.out.write("no action specfifed")
    if action == "testsearch":
      index = search.Index(name=_ITEM_INDEX)
      query_string = "distance(location, geopoint(33.08,-117.25)) < 5000"
      query = search.Query(query_string=query_string)
      doc = index.search(query)
      #doc = index.search("burger")
      self.response.out.write(doc)
    if action == "deferred":
      deferred.defer(something_expensive,"a","b","c")
      return self.response.out.write("added to queue")
    if action == "resetfood":
      deferred.defer(reset_food,"a","b","c")
      return self.response.out.write("reset!")
    #remove search documents that do not have a datastore entry anymore
    if action == "removeitemdocuments":
      doc_index = search.Index(name="items")
      for item in doc_index.get_range(ids_only=True):
        if not Item.get_by_id(int(item.doc_id)):
          doc_index.delete(item.doc_id)
      self.response.out.write("ok")
    if action == "removerestaurantdocuments":
      doc_index = search.Index(name="restaurants")
      for restaurant in doc_index.get_range(ids_only=True):
        if not Restaurant.get_by_id(int(restaurant.doc_id)):
          doc_index.delete(item.doc_id)
      self.response.out.write("ok")
    if action == "missing":
      for review in Review.all():
        try: review.date_edited
        except:
          review.date_edited = datetime.datetime.now()
          review.save()
      self.response.out.write("ok")
    if action == "following":
      for u in User.query():
        u.following = [
          43001,
          44001,
          45001,
          46001,
          109001
        ]
        u.followers = [
          43001,
          44001,
          45001,
          46001,
          109001
        ]
        u.put()
      self.response.out.write("ok")

