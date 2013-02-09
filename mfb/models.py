from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api.images import get_serving_url
from geo.geomodel import GeoModel

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

class Menu(db.Model):
    name = db.StringProperty(required = False) 
    restaurant = db.ReferenceProperty(Restaurant)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty(required = False)
    order = db.IntegerProperty(required = False)

class Item(db.Model):
    name = db.StringProperty(required = True)
    menu = db.ReferenceProperty(Menu)
    description = db.TextProperty(required = False)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty(required = False)
    order = db.IntegerProperty(required = False)

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
