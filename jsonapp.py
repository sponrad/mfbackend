import webapp2
from mfb.jsonhandlers import *

config = {
    'webapp2_extras.auth': {
        'user_model': 'mfb.models.User',
        'user_attributes': ['auth_ids', 'admin'],
        },
    'webapp2_extras.sessions': {
        'secret_key': 'THISKEYISSUCHASECRET',
        }
    }

app = webapp2.WSGIApplication([
        ('/json/location', GetLocation),    #latlong
        ('/json/locations', GetLocations),  #latlongradius
        ('/json/items', GetItems),
        ('/json/getmenu', GetMenu),         #locationid
        ('/json/getitem', GetItem),         #menuid, optional:locationid
        ('/json/reviewitem', ReviewItem),   #userid, authtoken, itemid, rating, description
        ('/json/profile', GetProfile),
        ('/json/createrestaurant', CreateRestaurant),
        ('/json/createitem', CreateItem),
        ('/json/signup', Signup),
        ('/json/login', Login),
        ('/json/logout', Logout),
        ('/json/signup', SignupHandler),
        ('/json/', Test),
        ('/json', Test),
], debug=True, config=config)
