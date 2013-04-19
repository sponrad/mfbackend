import os, datetime, random, string, urllib, math, globs, json
import webapp2
import os.path

from webapp2_extras import auth
from webapp2_extras import sessions
from google.appengine.ext.webapp import template

from models import *
from geo import geotypes

BINGKEY = globs.BINGKEY

def admin_required(handler):
  def check_admin(self, *args, **kwargs):
    auth = self.auth
    if not auth.get_user_by_session()['admin']:
      self.redirect(self.uri_for('home'))
    else:
      return handler(self, *args, **kwargs)

  return check_admin

#render(self, 'account.html', values)
def render(self, t, values = {}):
    if 'user' not in values:
        values['user'] = self.auth.get_user_by_session()
    try: values['referer'] = self.request.headers['Referer']
    except: values['referer'] = "/"
    templatefile = '_templates/' + t
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), templatefile)
    self.response.out.write(template.render(path, values))

class BaseHandler(webapp2.RequestHandler):
  @webapp2.cached_property
  def auth(self):
    """Shortcut to access the auth instance as a property."""
    return auth.get_auth()

  @webapp2.cached_property
  def user_info(self):
    """Shortcut to access a subset of the user attributes that are stored
    in the session.

    The list of attributes to store in the session is specified in
      config['webapp2_extras.auth']['user_attributes'].
    :returns
      A dictionary with most user information
    """
    return self.auth.get_user_by_session()

  @webapp2.cached_property
  def user(self):
    """Shortcut to access the current logged in user.

    Unlike user_info, it fetches information from the persistence layer and
    returns an instance of the underlying model.

    :returns
      The instance of the user model associated to the logged in user.
    """
    u = self.user_info
    return self.user_model.get_by_id(u['user_id']) if u else None

  @webapp2.cached_property
  def user_model(self):
    """Returns the implementation of the user model.

    It is consistent with config['webapp2_extras.auth']['user_model'], if set.
    """    
    return self.auth.store.user_model

  @webapp2.cached_property
  def session(self):
      """Shortcut to access the current session."""
      return self.session_store.get_session(backend="datastore")

  def render_template(self, view_filename, params={}):
    user = self.user_info
    params['user'] = user
    path = os.path.join(os.path.dirname(__file__), 'views', view_filename)
    self.response.out.write(template.render(path, params))

  def display_message(self, message):
    """Utility function to display a template with a simple message."""
    params = {
      'message': message
    }
    self.render_template('message.html', params)

  # this is needed for webapp2 sessions to work
  def dispatch(self):
      # Get a session store for this request.
      self.session_store = sessions.get_store(request=self.request)

      try:
          # Dispatch the request.
          webapp2.RequestHandler.dispatch(self)
      finally:
          # Save all sessions.
          self.session_store.save_sessions(self.response)

def get_lat_long(query):
    query = urllib.quote_plus(query)
    url ="http://dev.virtualearth.net/REST/v1/Locations?query=" + query + "&key=" + BINGKEY
    jsondata = json.loads(urllib.urlopen(url).read())

    #only want one result
    if len(jsondata['resourceSets'][0]['resources']) == 1: 
        return jsondata['resourceSets'][0]['resources'][0]['point']['coordinates']
    else:
        return None

def get_lat_long_city_state_address(query):
    query = urllib.quote_plus(query)
    url ="http://dev.virtualearth.net/REST/v1/Locations?query=" + query + "&key=" + BINGKEY
    jsondata = json.loads(urllib.urlopen(url).read())

    #check results exist, take first result
    if len(jsondata['resourceSets'][0]['resources']) > 0: 
        values = jsondata['resourceSets'][0]['resources'][0]['point']['coordinates']
        values.append(jsondata['resourceSets'][0]['resources'][0]['address']['locality'])  #CITY
        values.append(jsondata['resourceSets'][0]['resources'][0]['address']['adminDistrict'])  #STATE
        values.append(jsondata['resourceSets'][0]['resources'][0]['address']['addressLine']) #ADDRESS
        return values
    else:
        return None

def get_location_string(address = None, city = None, state = None, zipcode = None):
    string = ""
    if address: string = ",".join((string, address))
    if city: string = ",".join((string, city))
    if state: string = ",".join((string, state))
    if zipcode: string = ",".join((string, zipcode))
    return string

def queryfunctionfactory(min_price, max_price, min_sqft, max_sqft):
    #a list generator that will filter
    # [p for p in listings if queryfunction(p.office_sq_ft, p.price)]
    def queryfunction(price, sqft):
        if min_price:
            if price < min_price: return False
        if max_price:
            if price > max_price: return False
        if min_sqft:
            if sqft < min_sqft: return False
        if max_sqft:
            if sqft > max_sqft: return False
        return True
    return queryfunction
