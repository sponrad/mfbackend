import webapp2
from mfb.models import *
from mfb.handlers import *

app = webapp2.WSGIApplication([
        ('/restaurants', Restaurants),
        (r'/restaurant/(.*)', Locations),            
        (r'/locations/(.*)', Locations),
        ('/', MainHandler)
], debug=True)
