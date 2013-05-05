import os, webapp2, helpers, globs, json
from models import *
from geo import geotypes
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from helpers import *

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

def renderjson(self, values):
	self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(values))

class Login(BaseHandler):
	def get(self):
		username = self.request.get('username')
		password = self.request.get('password')
		try:
			u = self.auth.get_user_by_password(username, password, remember=False, save_session=False)
			auth_token = self.user_model.create_auth_token(u['user_id'])
			values = {
				"response": 1,
				"user_dict": u,
				"auth_token": auth_token,
				}
			renderjson(self, values)			
		except (InvalidAuthIdError, InvalidPasswordError) as e:
			self.response.out.write("exception")
		
class Logout(BaseHandler):
	def get(self):
		userid = self.request.get('userid')
		authtoken = self.request.get('authtoken')
		self.user_model.delete_auth_token(userid, authtoken)
		values = {
			"response": 1,
			}
		renderjson(self, values)

class SignupHandler(BaseHandler):
  def get(self):
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
      self.display_message('Unable to create user for email %s because of \
        duplicate keys %s' % (user_name, user_data[1]))
      return
    
    user = user_data[1]
    user_id = user.get_id()
    user.put()

    values = {
	    "response": 1,
	    }
    renderjson(self, values)

''' given a lat long, returns a single location for the flip screen '''
class LocationSearch(webapp2.RequestHandler):
    def get(self):
        latitude = self.request.get("latitude")
        longitude = self.request.get("longitude")
        if latitude != "" and longitude != "":
            locations = Location.all()
            locations = Location.proximity_fetch(
                locations,
                geotypes.Point(float(latitude), float(longitude)),
                max_results = 1,
                max_distance = 48,  #meters, this is ~150 feet
                )
            if locations: 
                location = locations[0]
                values = {
                    "locationname": str(location.name),
                    "location": [location.location.lat, location.location.lon],
                    "restaurant": str(location.restaurant.name),
		    "restaurantid": str(location.restaurant.key().id()),
                    "address": str(location.address),
                    "city": str(location.city),
		    "zip": str(location.zipcode),
		    "state": str(location.state),
                    }
            else:
                location = None
                values = "No Matches"

        else:
            locations = None
            values = "No matches"

        renderjson(self, values)
        

''' given a lat long and radius, returns nearby locations '''
class LocationsSearch(webapp2.RequestHandler):
    def get(self):
        values = {}
        latitude = self.request.get("latitude")
        longitude = self.request.get("longitude")
	radius = self.request.get("radius")
        if latitude != "" and longitude != "":
            locations = Location.all()
            locations = Location.proximity_fetch(
		    locations,
		    geotypes.Point(float(latitude), float(longitude)),
		    max_results = 30,
		    max_distance = int(float(radius)*0.3048),  #ft to meters
		    )
	    if len(locations) > 0: 
		    values['locations'] = []
		    values['response'] = 1
		    for l in locations:
			    locationdata = {
				    "locationname": str(l.name),
				    "location": [l.location.lat, l.location.lon],
				    "restaurant": str(l.restaurant.name),
				    "restaurantid": str(l.restaurant.key().id()),
				    "address": str(l.address),
				    "city": str(l.city),
				    "state": str(l.state),
				    "zip": str(l.zipcode),
				    }
			    values['locations'].append(locationdata)
            else:
		    location = None
		    values['response'] = 0

        else:
            locations = None
            values['response'] = 0

        renderjson(self, values)

class GetMenu(webapp2.RequestHandler):
	def get(self):
		restaurantid = self.request.get("restaurantid")
		restaurant = Restaurant.get_by_id(int(restaurantid))
		values = {}
		menus = []
		for menu in restaurant.menu_set:
			m = {}
			m['name'] = menu.name
			items = []		
			for item in menu.item_set:
				i = {}
				i['name'] = item.name
				i['description'] = item.description
				i['price'] = item.price
				i['itemid'] = item.key().id()
				items.append(i)
			m['items'] = items
			menus.append(m)
		values['menus'] = menus
			
		values['response'] = 1
		renderjson(self, values)

class GetItem(webapp2.RequestHandler):
	def get(self):
		itemid = self.request.get("itemid")
		item = Item.get_by_id(int(itemid))
		values = {
			"respnose": 1,
			"restaurant": item.menu.restaurant.name,
			"restaurantid": item.menu.restaurant.key().id(),
			"menu": item.menu.name,
			"menuid": item.menu.key().id(),
			"itemid": itemid,
			"name": item.name,
			"description": item.description,
			"price": item.price,
			"tags": item.tags,			
			"rating": item.rating(),
			}
		renderjson(self, values)

class ReviewItem(BaseHandler):
	def post(self):
		userid = self.request.get("userid")
		authtoken = self.request.get("authtoken")
		itemid = self.request.get("itemid")
		rating = self.request.get("rating")
		description = self.request.get("description")

		if rating == "1":
			rating = 100
		else if rating == "0":
			rating = 0

		user = self.auth.get_user_by_tokent(userid, authtoken)
		item = Item.get_by_id(int(itemid))
		review = Review(
			userid = user.key().id(),
			item = item,
			rating = rating,
			description = description,
			)
		review.put()
		values = {
			"response": 1,
			}
		renderjson(self, values)
		
class CreateRestaurant(webapp2.RequestHandler):
#given restaurant name 
#return id
    def get(self):
        if self.request.get("name") == "":
            renderjson(self, "Error, supply a name in the request")
        restaurant = Restaurant(
            name = self.request.get("name")
            )
        restaurant.put()
        if restaurant.key():
            values = restaurant.key().id()
            renderjson(self, values)
        else:
            renderjson(self, "Error on save, check data")

class CreateLocation(webapp2.RequestHandler):
#given restaurantid, name, address, city, state, zipcode
#return location id
    def get(self):
        restaurant = Restaurant.get_by_id(int(self.request.get("restaurantid")))
        location = Location(
            name = self.request.get("name"),
            address = self.request.get("address"),
            city = self.request.get("city"),
            zipcode = self.request.get("zipcode"),
            restaurant = restaurant,
            )
        location.updatelocation()
        location.put()
        if location.key():
            values = location.key().id()
            renderjson(self, values)
        else:
            renderjson(self, "Error on save")

class CreateMenu(webapp2.RequestHandler):
#given restaurantid, name
#return menu id
    def get(self):
        restaurant = Restaurant.get_by_id(int(self.request.get("restaurantid")))
        menu = Menu(
            name = self.request.get("name"),
            restaurant = restaurant,
            )
        menu.initialorder()
        menu.put()
        if menu.key():
            values = menu.key().id()
            renderjson(self, values)
        else:
            renderjson(self, "Error")

class CreateItem(webapp2.RequestHandler):
#given menuid, name, description, price
#return item id
    def get(self):
        menu = Menu.get_by_id(int(self.request.get("menuid")))
        item = Item(
            name = self.request.get("name"),
            description = self.request.get("description"),
            price = self.request.get("price"),
            menu = menu
            )
        item.put()
        if item.key():
            values = item.key().id()
            renderjson(self, values)
        else:
            renderjson(self, "Error on item add")

class Test(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Success")
