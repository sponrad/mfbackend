import os, webapp2, helpers, globs, json
from models import *
from geo import geotypes
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db

def renderjson(self, values):
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(values))

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
                max_distance = 20,  #meters
                )
            if locations: 
                location = locations[0]
                values = {
                    "locationname": str(location.name),
                    "location": [location.location.lat, location.location.lon],
                    "restaurant": str(location.restaurant.name),
                    "address": str(location.address),
                    "city": str(location.city),
                    }
            else:
                location = None
                values = "No Matches"

        else:
            locations = None
            values = "No matches"

        renderjson(self, values)
        

''' given a lat long, returns nearby locations '''
class LocationsSearch(webapp2.RequestHandler):
    def get(self):
        pass

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
#given menuid, name, description, cost
#return item id
    def get(self):
        menu = Menu.get_by_id(int(self.request.get("menuid")))
        item = Item(
            name = self.request.get("name"),
            description = self.request.get("description"),
            cost = self.request.get("cost"),
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
