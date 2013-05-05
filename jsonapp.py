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
        ('/json/location', GetLocation),
        ('/json/locations', GetLocations),
        ('/json/getmenu', GetMenu),
        ('/json/getitem', GetItem),
        ('/json/reviewitem', ReviewItem),
        ('/json/createrestaurant', CreateRestaurant),
        ('/json/createlocation', CreateLocation),
        ('/json/createmenu', CreateMenu),
        ('/json/createitem', CreateItem),
        ('/json/login', Login),
        ('/json/logout', Logout),
        ('/json/signup', SignupHandler),
        ('/json/', Test),
        ('/json', Test),
], debug=True, config=config)
