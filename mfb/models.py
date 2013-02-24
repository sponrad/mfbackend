from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api.images import get_serving_url
from geo.geomodel import GeoModel
import helpers

class Restaurant(db.Model):
    name = db.StringProperty(required = True)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty(required = False)

class Location(GeoModel):
    name =  db.StringProperty(required = False)
    restaurant = db.ReferenceProperty(Restaurant)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty(required = False)
    address = db.StringProperty(required = False)
    city = db.StringProperty(required = False)
    state = db.StringProperty(required = False)
    zipcode = db.StringProperty(required = False)
    
    def updatelocation(self):
        locationstring = helpers.get_location_string(address = self.address, zipcode = self.zipcode)
        latlongcitystate = helpers.get_lat_long_city_state_address(locationstring)
        if latlongcitystate: 
            self.location = db.GeoPt(latlongcitystate[0], latlongcitystate[1])
            self.city = latlongcitystate[2]
            self.state = latlongcitystate[3]
            self.address = latlongcitystate[4]
            self.update_location()        

class Menu(db.Model):
    name = db.StringProperty(required = False) 
    restaurant = db.ReferenceProperty(Restaurant)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty(required = False)
    order = db.IntegerProperty(required = False)

    def initialorder(self):
        self.order = self.restaurant.menu_set.count() + 1

class Item(db.Model):
    name = db.StringProperty(required = True)
    menu = db.ReferenceProperty(Menu)
    description = db.TextProperty(required = False)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty(required = False)
    order = db.IntegerProperty(required = False)
    cost = db.StringProperty(required = False)

class Tag(db.Model):
    name = db.StringProperty(required = False)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    
class Account(db.Model):
    user = db.UserProperty()
    email = db.StringProperty()
    passwordhash = db.StringProperty()
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
