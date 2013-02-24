import os, webapp2, helpers, globs, json
from models import *
from geo import geotypes
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db

providers = {
    'Google'   : 'https://www.google.com/accounts/o8/id',
    'Yahoo'    : 'yahoo.com',
    'MySpace'  : 'myspace.com',
    'AOL'      : 'aol.com',
    'MyOpenID' : 'myopenid.com'
    # add more here
}

#render(self, 'account.html', values)
def render(self, t, values):
    if values["user"]:  # signed in already
        values["logout"] = users.create_logout_url(self.request.uri)
    else:     # let user choose authenticator
        values["logins"] = []
        for name, uri in providers.items():
            url = users.create_login_url(federated_identity=uri)
            temp = {"name": name, "url": url }
            values["logins"].append(temp)
    try: values['referer'] = self.request.headers['Referer']
    except: values['referer'] = "/"
    if users.is_current_user_admin():
        values['admin'] = True
    templatefile = '_templates/' + t
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), templatefile)
    self.response.out.write(template.render(path, values))

######################## HANDLERS

class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        values = {"user": user}
        render(self, 'home.html', values)

class Restaurants(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        restaurants = Restaurant.all().run()
        values = {
            "user": user,
            "restaurants": restaurants,
            }
        render(self, "restaurants.html", values)
    def post(self):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        restaurant = Restaurant(
            name = self.request.get("name")
            )
        restaurant.put()
        defaultmenu = Menu(
            restaurant = restaurant,
            name = str(restaurant.name).title() + " Default Menu",
            )
        defaultmenu.put()
        self.redirect('/restaurant/' + str(restaurant.key().id()))

class RestaurantPage(webapp2.RequestHandler):
    def get(self, restaurantid):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        restaurant = Restaurant.get_by_id(int(restaurantid))
        locations = Location.all().filter("restaurant =", restaurant).run()
        values = {
            "user": user,
            "restaurant": restaurant,
            "locations": locations,
            }
        render(self, "restaurant.html", values)
    def post(self, restaurantid):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        restaurant = Restaurant.get_by_id(int(restaurantid))
        location = Location(
            name = self.request.get("name"),
            address = self.request.get("address"),
            city = self.request.get("city"),
            zipcode = self.request.get("zipcode"),
            restaurant = restaurant,
            )
        location.updatelocation()
        location.put()
        self.redirect("/restaurant/" + str(restaurant.key().id()))
        
class RestaurantItems(webapp2.RequestHandler):
    def get(self, restaurantid):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        values = {
            "user": user,
            }
        restaurant = Restaurant.get_by_id(int(restaurantid))
        values["restaurant"] = restaurant
        render(self, "items.html", values)
    def post(self, restaurantid):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        restaurant = Restaurant.get_by_id(int(restaurantid))
        if self.request.get("action") == "addmenu":
            menu = Menu(
                name = self.request.get("name"),
                restaurant = restaurant,
                )
            menu.put()
        if self.request.get("action") == "additem":
            menu = Menu.get_by_id(int(self.request.get("menu")))
            item = Item(
                name = self.request.get("name"),
                description = self.request.get("description"),
                menu = menu
                )
            item.put()
        values = {
            "user": user,
            }
        self.redirect("/items/" + str(restaurant.key().id()))

class SearchLocation(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        results = None

        locationstring = self.request.get("location")
        locationlatlong = None
        querystring = self.request.get("query")
        miles = 5

        #start our query
        if locationstring != "":
            locations = Location.all()
        else:
            locations = None

        if querystring != "":
            pass
        else:
            querystring = None

        if locationstring != "":
            latlong = helpers.get_lat_long(locationstring)
            if latlong:
                locations = Location.proximity_fetch(
                    locations,
                    geotypes.Point(latlong[0], latlong[1]),
                    max_results = 100,
                    max_distance = (1609 * int(miles)), #1609 meters in a mile
                    )
                locationlatlong = latlong
        else:
            locationstring = None

        results = locations

        values = {
            "user": user,
            "results": results,
            "locationstring": locationstring,
            "locationlatlong": locationlatlong,
            "querystring": querystring,
            "miles": str(miles),
            "message": "Locations",
            }
        render(self, "search.html", values)

class SearchItem(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            self.redirect("/")
        results = None

        values = {
            "user": user,
            "results": results,
            "locationstring": None,
            "querystring": None,
            "miles": 0,
            "message": "Item search not working yet, also make a different template."
            }
        render(self, "search.html", values)        
