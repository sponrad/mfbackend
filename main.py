import webapp2
from mfb.models import *
from mfb.handlers import *

app = webapp2.WSGIApplication([
        ('/restaurants', Restaurants),
        (r'/restaurant/(.*)', RestaurantPage),
        (r'/items/(.*)', RestaurantItems),
        ('/search', Search),
        ('/', MainHandler)
], debug=True)
