import os, webapp2, helpers, globs, json
from models import *
from geo import geotypes
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db

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


        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(values))
        

''' given a lat long, returns nearby locations '''
class LocationsSearch(webapp2.RequestHandler):
    def get(self):
        pass

class CreateRestaurant(webapp2.RequestHandler):
#given restaurant name 
#returns id
    def get(self):
        pass

class CreateLocation(webapp2.RequestHandler):
#given name, address, city, state, zipcode
#returns location id
    def get(self):
        pass

class CreateMenu(webapp2.RequestHandler):
    def get(self):
        pass

class CreateItem(webapp2.RequestHandler):
    def get(self):
        pass

class Test(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Success")
