from google.appengine.ext import db, ndb, blobstore
from google.appengine.api.images import get_serving_url
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
from geo.geomodel import GeoModel
import helpers, time

class User(webapp2_extras.appengine.auth.models.User):
    '''
    admin
    auth_ids
    email_address
    password (hash)
    name
    last_name
    '''
    friends = db.StringListProperty()
    
    def set_password(self, raw_password):
        """Sets the password for the current user
        :param raw_password:
        The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)
    
    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.

        :param user_id:
        The user_id of the requesting user.
        :param token:
        The token string to be verified.
        :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp

        return None, None

class Restaurant(db.Model):
    name = db.StringProperty(required = True)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty()

class Location(GeoModel):
    name =  db.StringProperty()
    restaurant = db.ReferenceProperty(Restaurant)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty()
    address = db.StringProperty()
    city = db.StringProperty()
    state = db.StringProperty()
    zipcode = db.StringProperty()
    phonenumber = db.StringProperty()
    tags = db.StringListProperty()
    
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
    name = db.StringProperty() 
    restaurant = db.ReferenceProperty(Restaurant)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty()
    order = db.IntegerProperty()

    def initialorder(self):
        self.order = self.restaurant.menu_set.count() + 1

class Item(db.Model):
    name = db.StringProperty(required = True)
    menu = db.ReferenceProperty(Menu)
    description = db.TextProperty()
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty()
    order = db.IntegerProperty()
    price = db.StringProperty()
    tags = db.StringListProperty()
