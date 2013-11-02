import helpers, time, globs
from google.appengine.ext import db, ndb, blobstore
from google.appengine.api.images import get_serving_url
from google.appengine.api import search
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
from geo.geomodel import GeoModel

_RESTAURANT_INDEX = globs._RESTAURANT_INDEX
_ITEM_INDEX = globs._ITEM_INDEX

class User(webapp2_extras.appengine.auth.models.User):
    '''
    admin
    auth_ids
    email_address
    password (hash)
    name
    last_name
    numberofratings
    following?
    followers?
    followedlists?
    '''
    
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

class State(db.Model):
    name = db.StringProperty()
    abb = db.StringProperty()
    cities = db.StringListProperty(default = [])

class Restaurant(db.Model):
    name = db.StringProperty(required = True)
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty()
    numberofitems = db.IntegerProperty(default=0)
    numberofreviews = db.IntegerProperty(default=0)
    completecheck = db.BooleanProperty(default = False)
    location = db.GeoPtProperty() #location.lat, location.lon
    address = db.StringProperty()
    city = db.StringProperty()
    zipcode = db.StringProperty()
    phonenumber = db.StringProperty()
    tags = db.StringListProperty()

    def updatelocation(self, locationstring):
        locationstring = helpers.get_location_string(address = self.address, zipcode = self.zipcode)
        latlongcitystate = helpers.get_lat_long_city_state_address(locationstring)
        if latlongcitystate: 
            self.location = db.GeoPt(latlongcitystate[0], latlongcitystate[1])
            self.city = latlongcitystate[2]
            self.state = latlongcitystate[3]
            self.address = latlongcitystate[4]
            self.update_location()    
            
    def delete(self):
        #delete from the search index
        doc_index = search.Index(name=_RESTAURANT_INDEX)
        doc_index.delete(str(self.key().id()))
        for item in self.item_set:
            item.delete()
        db.delete(self.key())

    def updateindex(self):
        helpers.createrestaurantdocument(self)

class Item(db.Model):
    name = db.StringProperty(required = True)
    restaurant = db.ReferenceProperty(Restaurant)
    description = db.TextProperty()
    date_created = db.DateTimeProperty(auto_now_add = True)
    date_edited = db.DateTimeProperty(auto_now = True)
    slug = db.StringProperty()
    order = db.IntegerProperty()
    price = db.StringProperty()
    tags = db.StringListProperty()
    numberofreviews = db.IntegerProperty(default=0)

    def rating(self):
        total = 0
        count = 0
        for rating in self.review_set:
            total += rating.rating
            count += 1
        try:
            rating = int(round(total/count))
        except:
            rating = 0
        return rating
            
    def delete(self):
        #delete from the search index
        doc_index = search.Index(name=_ITEM_INDEX)
        doc_index.delete(str(self.key().id()))
        for review in self.review_set:
            review.delete()
        self.restaurant.numberofitems -= 1
        self.restaurant.put()
        db.delete(self.key())

    def updateindex(self):
        helpers.createitemdocument(self, self.restaurant)        

class Review(db.Model):
    userid = db.IntegerProperty()
    item = db.ReferenceProperty(Item)
    rating = db.IntegerProperty() #0 bad 100 good
    description = db.TextProperty()
    image = db.BlobProperty()

class Chain(db.Model):
    name = db.StringProperty(required = True)
    restaurantids = db.StringListProperty(int)

class List(db.Model):
    name = db.StringProperty(required = True)
    userid = db.IntegerProperty()
    itemids = db.StringListProperty()
    followerids = db.StringListProperty()
