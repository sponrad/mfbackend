from helpers import *
from models import *
from geo import geotypes

providers = {
    'Google'   : 'https://www.google.com/accounts/o8/id',
#    'Yahoo'    : 'yahoo.com',
#    'MyOpenID' : 'myopenid.com'
}

######################## HANDLERS
class SignupHandler(BaseHandler):
  def post(self):
    user_name = self.request.get('username')
    email = self.request.get('email')
    name = self.request.get('name')
    password = self.request.get('password')
    last_name = self.request.get('lastname')

    unique_properties = ['email_address']
    user_data = self.user_model.create_user(user_name,
      unique_properties,
      email_address=email, name=name, password_raw=password,
      last_name=last_name, verified=False)
    if not user_data[0]: #user_data is a tuple
      self.display_message('Unable to create user for email %s because of \
        duplicate keys %s' % (user_name, user_data[1]))
      return
    
    user = user_data[1]
    user_id = user.get_id()
    user.put()
    #token = self.user_model.create_signup_token(user_id)

    #verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)

      #msg = 'Send an email to user in order to verify their address. \They will be able to do so by visiting <a href="{url}">{url}</a>'

    #self.display_message(msg.format(url=verification_url))
    self.redirect(self.uri_for('home'))

class LoginHandler(BaseHandler):
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        try:
            u = self.auth.get_user_by_password(username, password, remember=True,
                                               save_session=True)
            self.redirect(self.uri_for('home'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self.redirect(self.uri_for('home'))
            
class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect(self.uri_for('home'))

class MainHandler(BaseHandler):
    def get(self):
        user = self.auth.get_user_by_session()
        values = {
            }
        render(self, 'home.html', values)

class Restaurants(BaseHandler):
    @admin_required
    def get(self):
        restaurants = Restaurant.all().run()
        values = {
            "restaurants": restaurants,
            }
        render(self, "restaurants.html", values)
    @admin_required
    def post(self):
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

class RestaurantPage(BaseHandler):
    @admin_required
    def get(self, restaurantid):
        restaurant = Restaurant.get_by_id(int(restaurantid))
        locations = Location.all().filter("restaurant =", restaurant).run()
        values = {
            "restaurant": restaurant,
            "locations": locations,
            }
        render(self, "restaurant.html", values)
    @admin_required
    def post(self, restaurantid):
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
        
class RestaurantItems(BaseHandler):
    @admin_required
    def get(self, restaurantid):
        restaurant = Restaurant.get_by_id(int(restaurantid))
        values = {
            "restaurant": restaurant,
            }
        render(self, "items.html", values)
    @admin_required
    def post(self, restaurantid):
        restaurant = Restaurant.get_by_id(int(restaurantid))
        if self.request.get("action") == "addmenu":
            menu = Menu(
                name = self.request.get("name"),
                restaurant = restaurant,
                )
            menu.initialorder()
            menu.put()
        if self.request.get("action") == "additem":
            menu = Menu.get_by_id(int(self.request.get("menu")))
            item = Item(
                name = self.request.get("name"),
                description = self.request.get("description"),
                menu = menu
                )
            item.put()
        self.redirect("/items/" + str(restaurant.key().id()))

class SearchLocation(BaseHandler):
    @admin_required
    def get(self):
        results = None

        locationstring = self.request.get("location")
        locationlatlong = None
        querystring = self.request.get("query")
        radius = self.request.get("radius")

        #start our query
        if locationstring != "":
            locations = Location.all()
        else:
            locations = None

        if querystring != "":
            pass
        else:
            querystring = None

        if radius == "":
            radius = 0

        if locationstring != "":
            latlong = get_lat_long(locationstring)
            if latlong:
                locations = Location.proximity_fetch(
                    locations,
                    geotypes.Point(latlong[0], latlong[1]),
                    max_results = 100,
                    max_distance = (0.3048 * float(radius)),
                    )
                locationlatlong = latlong
        else:
            locationstring = None

        results = locations

        values = {
            "results": results,
            "locationstring": locationstring,
            "locationlatlong": locationlatlong,
            "querystring": querystring,
            "feetstring": str(radius),
            "milestring": str(float(radius) / 5280),
            "message": "Locations",
            }
        render(self, "search.html", values)

class SearchItem(BaseHandler):
    @admin_required
    def get(self):
        results = None

        values = {
            "results": results,
            "locationstring": None,
            "querystring": None,
            "miles": 0,
            "message": "Item search not working yet, also make a different template."
            }
        render(self, "search.html", values)        
