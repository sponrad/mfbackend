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
        ('/json/items', GetItems),
        ('/json/restaurants', GetRestaurants),
        ('/json/getmenu', GetMenu),         #restaurantid
        ('/json/getitem', GetItem),         #menuid, optional:locationid
        ('/json/profile', GetProfile),

        ('/json/reviewitem', ReviewItem),   #userid, authtoken, itemid, rating, description
        ('/json/createrestaurant', CreateRestaurant),
        ('/json/createitem', CreateItem),

        ('/json/signup', Signup),
        ('/json/login', Login),
        ('/json/logout', Logout),
        ('/json/signup', SignupHandler),
        ('/json/', Test),
        ('/json', Test),
], debug=True, config=config)
