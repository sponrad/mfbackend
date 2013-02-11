import webapp2
from mfb.jsonhandlers import *

app = webapp2.WSGIApplication([
        ('/json/location', LocationSearch),
        ('/json/locations', LocationsSearch),
        ('/json', Test),
], debug=True)
