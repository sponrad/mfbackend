import webapp2
from mfb.handlers import *

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
        ('/restaurants', Restaurants),
        (r'/restaurant/(.*)', RestaurantPage),
        (r'/items/(.*)', RestaurantItems),
        ('/locations', Locations),
        ('/searchlocations', SearchLocation),
        ('/signup', SignupHandler),
        ('/login', LoginHandler),
        ('/logout', LogoutHandler),
        ('/editable', Editable),
        ('/delete', Delete),
        ('/maintain', Maintain),
         webapp2.Route('/', MainHandler, name="home")
], debug=True, config=config)
