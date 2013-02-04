import webapp2
from mfb.models import *
from mfb.handlers import *

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
