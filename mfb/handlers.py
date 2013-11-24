from helpers import *
import helpers
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
        render(self, 'home.html', values)

class Password(BaseHandler):
  def get(self):
    user = self.auth.get_user_by_session()
    message = self.request.get("m")
    values = {
      "message": message if message else None
      }
    render(self, 'password.html', values)
  def post(self):
    username = self.request.get("username")
    rawpassword = self.request.get("password")
    rawpasswordcheck = self.request.get("password2")
    if not rawpassword == rawpasswordcheck:
      return self.redirect("/password")
    user = User.get_by_auth_id(username)
    user.password = security.generate_password_hash(rawpassword)
    user.put()
    self.redirect("/password?m=done")


class Restaurants(BaseHandler):
    @admin_required
    def get(self):
        restaurants = Restaurant.all().run()
        values = {
            "restaurants": restaurants,
            }
        render(self, "restaurants.html", values)
    @admin_required
    def post(self):
        restaurant = Restaurant(
            name = self.request.get("name"),
            numberofitems = 0
            )
        restaurant.put()
        helpers.createrestaurantdocument(restaurant)
        self.redirect('/restaurant/' + str(restaurant.key().id()))

class RestaurantPage(BaseHandler):
    @admin_required
    def get(self, restaurantid):
      restaurant = Restaurant.get_by_id(int(restaurantid))
      values = {
        "restaurant": restaurant,
        }
      render(self, "restaurant.html", values)
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
      self.redirect('/restaurant/' + str(restaurant.key().id()))

class Cards(BaseHandler):
  @admin_required
  def get(self):
    cards = Card.all().run()
    values = {
      "cards": cards,
      }
    render(self, 'cards.html', values)
  def post(self):
    if self.request.get("action") == "addcard":
      card = Card(
        name = self.request.get("name"),
        ratingvalue = int(self.request.get("ratingvalue"))        
        )
      card.put()
      self.redirect("/cards")
        
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
      self.redirect("/restaurants")
    if action == "item":
      item = Item.get_by_id(int(id))
      restaurant = item.restaurant
      item.delete()
      restaurant.numberofitems -= 1
      restaurant.put()

      self.redirect("/restaurant/" + str(restaurant.key().id()))

class Maintain(BaseHandler):
  @admin_required
  def get(self):
    action = self.request.get("a")
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

