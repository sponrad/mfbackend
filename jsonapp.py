import webapp2
from mfb.jsonhandlers import *

app = webapp2.WSGIApplication([
        ('/json/location', LocationSearch),
        ('/json/locations', LocationsSearch),
        ('/json', Test),
        ('/json/createrestaurant', CreateRestaurant),
        ('/json/createlocation', CreateLocation),
        ('/json/createmenu', CreateMenu),
        ('/json/createitem', CreateItem),
], debug=True)
