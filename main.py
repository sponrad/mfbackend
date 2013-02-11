import webapp2
from mfb.handlers import *

app = webapp2.WSGIApplication([
        ('/restaurants', Restaurants),
        (r'/restaurant/(.*)', RestaurantPage),
        (r'/items/(.*)', RestaurantItems),
        ('/searchlocations', SearchLocation),
        ('/searchitems', SearchItem),
        ('/', MainHandler)
], debug=True)
