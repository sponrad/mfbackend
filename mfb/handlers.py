from helpers import *
from models import *
from geo import geotypes
import globs

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

providers = {
    'Google'   : 'https://www.google.com/accounts/o8/id',
#    'Yahoo'    : 'yahoo.com',
#    'MyOpenID' : 'myopenid.com'
}

DEFAULTMENUS = globs.DEFAULT_MENUS

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
      last_name=last_name, verified=False, admin=False)
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
            name = self.request.get("name"),
            numberofitems = 0
            )
        restaurant.put()
        for i in range(len(DEFAULTMENUS)):
          menu = Menu(
            restaurant = restaurant,
            name = DEFAULTMENUS[i],
            order = i+1,
            )
          menu.put()
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
        restaurant.put()
        self.redirect("/restaurant/" + str(restaurant.key().id()))
        
class RestaurantItems(BaseHandler):
    @admin_required
    def get(self, restaurantid):
        restaurant = Restaurant.get_by_id(int(restaurantid))
        values = {
            "restaurant": restaurant,
            "menus": restaurant.menu_set.order('order')
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
            restaurant.put()
        if self.request.get("action") == "additem":
            menu = Menu.get_by_id(int(self.request.get("menu")))
            item = Item(
                name = self.request.get("name"),
                description = self.request.get("description"),
                price = self.request.get("price"),
                menu = menu
                )
            item.put()
            restaurant.numberofitems += 1
            restaurant.put()
        if self.request.get("action") == "moveitem":
          itemid = self.request.get("itemid")
          item = Item.get_by_id(int(itemid))
          menu = Menu.get_by_id(int(self.request.get("tomenu")))
          item.menu = menu
          item.put()
          menu.put()
          restaurant.put()
        self.redirect("/items/" + str(restaurant.key().id()))

class Locations(BaseHandler):
  @admin_required
  def get(self):
    state = self.request.get("state")
    city = self.request.get("city")
    
    cities = None
    states = sorted(globs.states.keys())

    locations = Location.all()

    if state == "" and city == "":
      locations = None
    elif city == "":
      #get list of cities from results in the state
      cities = State.all().filter("abb =", state).get().cities
      locations = None
    elif state == "":
      locations = None      
    else:
      #get specific locations
      locations = locations.filter("state =", state).filter("city =", city).run()

    values = {
      "locations": locations,
      "states": states,
      "cities": cities,
      "state": state,
      "city": city
      }
    render(self, "locations.html", values)
  
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

class Editable(BaseHandler):
  @admin_required
  def get(self):
    self.response.out.write("there you are")
  @admin_required
  def post(self):
    id, action = self.request.get('id').split(".")
    value = self.request.get('value')
    if action == "restaurant_name":
      restaurant = Restaurant.get_by_id(int(id))
      restaurant.name = value
      restaurant.put()
      self.response.out.write(value)
    if action == "location_name":
      location = Location.get_by_id(int(id))
      location.name = value
      location.put()
      location.restaurant.put()
      self.response.out.write(value)
    if action ==  "location_address":
      #set the location, recalc the geohash
      location = Location.get_by_id(int(id))
      location.address = value.split(",").replace(" ", "")[0]
      location.city = value.split(",").replace(" ", "")[1]
      location.zipcode = value.split(",").replace(" ", "")[2]
      location.updatelocation()
      location.put()
      location.restaurant.put()
      self.response.out.write(value)
    if action == "menu_name":
      menu = Menu.get_by_id(int(id))
      menu.name = value
      menu.put()
      menu.restaurant.put()
      self.response.out.write(value)
    if action == "item_name":
      item = Item.get_by_id(int(id))
      item.name = value
      item.put()
      item.menu.restaurant.put()
      self.response.out.write(value)
    if action == "item_description":
      item = Item.get_by_id(int(id))
      item.description = value
      item.put()
      item.menu.restaurant.put()
      self.response.out.write(value)
    if action == "item_price":
      item = Item.get_by_id(int(id))
      item.price = value
      item.put()
      item.menu.restaurant.put()
      self.response.out.write(value)
    if action == "menu_order":
      menu = Menu.get_by_id(int(id))
      menu.order = int(value)
      menu.put()
      menu.restaurant.put()
      self.response.out.write(value)

class Delete(BaseHandler):
  @admin_required
  def get(self):
    action = self.request.get("action")
    id = self.request.get("id")
    if action == "restaurant":
      restaurant = Restaurant.get_by_id(int(id))
      restaurant.delete()
      self.redirect("/restaurants")
    if action == "location":
      location = Location.get_by_id(int(id))
      city = location.city
      state = location.state
      restaurant = location.restaurant
      location.delete()
      restaurant.put()
      self.redirect("/locations?state=" + state + "&city=" + city )
    if action == "menu":
      menu = Menu.get_by_id(int(id))
      restaurant = menu.restaurant
      menu.delete()
      restaurant.put()
      self.redirect("/items/" + str(restaurant.key().id()))
    if action == "item":
      item = Item.get_by_id(int(id))
      restaurant = item.menu.restaurant
      item.delete()
      restaurant.numberofitems -= 1
      restaurant.put()
      self.redirect("/items/" + str(restaurant.key().id()))

class Maintain(BaseHandler):
  @admin_required
  def get(self):
    action = self.request.get("a")
    if action == "ryanandpat":
      pat = User.get_by_auth_id('psdower')
      pat.admin = True
      pat.put()
      ryan = User.get_by_auth_id('ryanmunger')
      ryan.admin = True
      ryan.put()
      return self.response.out.write("done, ryan and pat are admin")
    if action == "itemcounts":
      restaurants = Restaurant.all().run()
      for r in restaurants:
        total = 0
        for m in r.menu_set:
          total += m.item_set.count()
        r.numberofitems = total
        r.put()
      return self.response.out.write("done")
    if action == "setstates":
      states = globs.states
      for abb in globs.states.keys():
        state = State(
          abb = abb,
          name = globs.states[abb],
          cities = []
          )
        state.put()
      return self.response.out.write("states added")
    if action == "setcities": #need to run this when adding new cities
      locations = Location.all().run()
      for l in locations:
        state = State.all().filter("abb =", l.state).get()
        if l.city not in state.cities:
          state.cities.append(l.city)
          state.put()
      return self.response.out.write("added all cities")
    if action == "":
      return self.response.out.write("no action specfifed")
