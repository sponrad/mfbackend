import os, webapp2, helpers, globs, json, re
from models import *
from geo import geotypes
from google.appengine.api import users, search
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import helpers
from helpers import *

from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

_ITEM_INDEX = globs._ITEM_INDEX
_RESTAURANT_INDEX = globs._RESTAURANT_INDEX

def renderjson(self, values):
	self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(values))

class Signup(BaseHandler):
	def post(self):
		user_name = self.request.get('username')
		email = self.request.get('email')
		password = self.request.get('password')
		passwordtwo = self.request.get('passwordtwo')

		if password != passwordtwo:
			values = {
				"response": 0,
				"message": "Passwords do not match",
				}		
			return renderjson(self, values)		

		if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
			values = {
				"response": 0,
				"message": "Bad email format",
				}		
			return renderjson(self, values)	

		unique_properties = ['email_address']
		user_data = self.user_model.create_user(
			user_name,
			unique_properties,
			email_address=email,
			password_raw=password,
			verified=False, 
			admin=False,
                        following=[],
			)
		if not user_data[0]: #user_data is a tuple
			values = {
				"response": 0,
				"message": "Username or email already exists",
				}
			return renderjson(self, values)	

		user = user_data[1]
		user_id = user.get_id()
                user.following.append(user_id)
		user.put()
    #token = self.user_model.create_signup_token(user_id)

    #verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)

      #msg = 'Send an email to user in order to verify their address. \They will be able to do so by visiting <a href="{url}">{url}</a>'

    #self.display_message(msg.format(url=verification_url))
		values = {
			"response": 1,
			}
		renderjson(self, values)			

class Login(BaseHandler):
	def post(self):
		self.response.headers['Access-Control-Allow-Origin'] = '*'
		username = self.request.get('username')
		password = self.request.get('password')
		try:
			u = self.auth.get_user_by_password(username, password, remember=False, save_session=False)
			auth_token = self.user_model.create_auth_token(u['user_id'])
			values = {
				"response": 1,
				"user_dict": u,
				"auth_token": auth_token,
				}
			renderjson(self, values)			
		except (InvalidAuthIdError, InvalidPasswordError) as e:
			self.response.out.write("exception")
		
class Logout(BaseHandler):
	def get(self):
		self.response.headers['Access-Control-Allow-Origin'] = '*'
		userid = self.request.get('userid')
		authtoken = self.request.get('authtoken')
		self.user_model.delete_auth_token(int(userid), authtoken)
		values = {
			"response": 1,
			}
		renderjson(self, values)

class SignupHandler(BaseHandler):
  def post(self):
    self.response.headers['Access-Control-Allow-Origin'] = '*'
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

    values = {
	    "response": 1,
	    }
    renderjson(self, values)

''' given a lat long and radius, returns nearby restaurants '''
class GetRestaurants(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        values = {}
        lat = self.request.get("latitude")
        lon = self.request.get("longitude")
	radius = self.request.get("radius")
	offset = self.request.get("offset")
	limit = self.request.get("limit")
	querystring = self.request.get("querystring")

	index = search.Index(name=_RESTAURANT_INDEX)
	
	query_string = "distance(location, geopoint(" + lat + "," + lon + ")) < " + radius

	if querystring:
		query_string += " AND " + querystring

	if not lat and not lon:
		return self.response.out.write("lat and long")
	
	expr1 = search.FieldExpression(name='distance', expression='distance(location, geopoint(' + lat + ',' + lon +'))')
	#sort1 = search.SortExpression(expression='distance', direction=SortExpression.DESCENDING, default_value=0)
	#sort_opts = search.SortOptions(expressions=[sort1])
	
	query_options = search.QueryOptions(
		returned_fields = ['name'],
		returned_expressions=[expr1],
		#sort_options= sort_opts
		)

	query = search.Query(
		query_string=query_string, 
		options=query_options
		)

	results = index.search(query)
	restaurants = []

	for scored_document in results.results:
		restaurant = {
			"restaurantid": scored_document.doc_id
			}
		for field in scored_document.fields:
			restaurant[field.name] = field.value
		for field in scored_document.expressions:
			restaurant[field.name] = field.value
	
		restaurants.append(restaurant)

	values['restaurants'] = restaurants
	values['response'] = 1

	#self.response.out.write(results.results[0].expressions[0].name)
	#self.response.out.write(results.results)

        renderjson(self, values)

''' given a lat long and radius, returns nearby Items '''
class GetItems(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        values = {}
        lat = self.request.get("latitude")
        lon = self.request.get("longitude")
	radius = self.request.get("radius")
	offset = self.request.get("offset")
	limit = self.request.get("limit")
	querystring = self.request.get("querystring")
	restaurantname = self.request.get("restaurantname")

	index = search.Index(name=_ITEM_INDEX)
	
	query_string = "distance(location, geopoint(" + lat + "," + lon + ")) < " + radius

	if querystring and restaurantname:
		query_string += " AND restaurantname: " + restaurantname + " AND " + querystring

	if not lat and not lon:
		return self.response.out.write("lat and long")
	
	expr1 = search.FieldExpression(name='distance', expression='distance(location, geopoint(' + lat + ',' + lon +'))')
	#sort1 = search.SortExpression(expression='distance', direction=SortExpression.DESCENDING, default_value=0)
	#sort_opts = search.SortOptions(expressions=[sort1])
	
	query_options = search.QueryOptions(
		returned_fields = ['name', 'rating', 'restaurantname'],
		returned_expressions=[expr1],
		#sort_options= sort_opts
		)

	query = search.Query(
		query_string=query_string, 
		options=query_options
		)
	results = index.search(query)
	items = []

	for scored_document in results.results:
		restaurantid = Item.get_by_id(int(scored_document.doc_id)).restaurant.key().id()
		item = {
			"itemid": scored_document.doc_id,
			"restaurantid": restaurantid
			}
		for field in scored_document.fields:
			item[field.name] = field.value
		for field in scored_document.expressions:
			item[field.name] = field.value
	
		items.append(item)

	values['items'] = items
	values['response'] = 1

	#self.response.out.write(results.results[0].expressions[0].name)
	#self.response.out.write(results.results)

        renderjson(self, values)

class GetMenu(webapp2.RequestHandler):
	def get(self):
		userid = self.request.get("userid")
		authtoken = self.request.get("authtoken")

		restaurantid = self.request.get("restaurantid")
		restaurant = Restaurant.get_by_id(int(restaurantid))
		values = {}
		items = []
		for item in restaurant.item_set:
			i = {}
			i['name'] = item.name
			i['description'] = item.description
			i['price'] = item.price
			i['itemid'] = item.key().id()
			i['rating'] = item.rating()
			items.append(i)
		values['items'] = items
		values['restaurantid'] = restaurant.key().id(),
		values['restaurantname'] = restaurant.name
		values['phonenumber'] = restaurant.phonenumber
		values['city'] = restaurant.city
		values['address'] = restaurant.address
		values['zipcode'] = restaurant.zipcode
		values['response'] = 1
		renderjson(self, values)

class GetItem(webapp2.RequestHandler):
	def get(self):
		itemid = self.request.get("itemid")
		item = Item.get_by_id(int(itemid))
		restaurant = item.restaurant
		values = {
			"response": 1,
			"restaurantname": item.restaurant.name,
			"restaurantid": item.restaurant.key().id(),
			"itemid": itemid,
			"name": item.name,
			"description": item.description,
			"price": item.price,
			"tags": item.tags,			
			"rating": item.rating(),
			}
		values['phonenumber'] = restaurant.phonenumber
		values['city'] = restaurant.city
		values['address'] = restaurant.address
		values['zipcode'] = restaurant.zipcode
		renderjson(self, values)

class GetItemSuggestions(BaseHandler):
	def get(self):
		latitude = self.request.get("latitude")
		longitude = self.request.get("longitude")
		querystring = self.request.get("query")
		doc_index = search.Index(name=_ITEM_INDEX)
		results = index.search(search.Query(query_string=querystring))

class GetRestaurantSuggestions(BaseHandler):
	def get(self):
		latitude = self.request.get("latitude")
		longitude = self.request.get("longitude")
		querystring = self.request.get("query")
		doc_index = search.Index(name=_ITEM_INDEX)
		results = index.search(search.Query(query_string=querystring))

class GetRestaurantId(BaseHandler):
	#given a lat long and a name of a restaurant, return an id and a name
	def get(self):
		#also send name of restaurant?
		restaurantname = self.request.get("restaurantname")
		lat = self.request.get("latitude")
		lon = self.request.get("longitude")

		values = {}

		query_string = "name = ~" + restaurantname + " AND distance(location, geopoint(" + lat + "," + lon + ")) < " + str(100000)
		#query_string = "distance(location, geopoint(" + lat + "," + lon + ")) < " + str(100)

		doc_index = search.Index(name=_RESTAURANT_INDEX)

		query_options = search.QueryOptions(
			returned_fields = ['name'],
			)

		query = search.Query(
			query_string=query_string, 
			options=query_options
			)

		results = doc_index.search(query)

		restaurants = []

		if results.number_found == 0:
			restaurant = Restaurant(
				name = restaurantname
				)
			restaurant.location = db.GeoPt(lat, lon)
			restaurant.put()
			restaurant.updateindex()
			restaurants.append({
					"restaurantid": restaurant.key().id(),
					"name": restaurant.name
					})

		else:
			for scored_document in results.results:
				restaurant = {
					"restaurantid": scored_document.doc_id
					}
				for field in scored_document.fields:
					restaurant[field.name] = field.value
				for field in scored_document.expressions:
					restaurant[field.name] = field.value
						
				restaurants.append(restaurant)


		values['restaurants'] = restaurants
		values['response'] = 1

		renderjson(self, values)
		
		
class ReviewItem(webapp2.RequestHandler):
	def options(self):
		self.response.headers['Access-Control-Allow-Origin'] = '*'
		self.response.headers['Access-Control-Allow-Headers'] = "Origin, X-Requested-With, Content-Type, Accept"

	def post(self):
		self.response.headers.add_header('Access-Control-Allow-Origin', '*')
		userid = self.request.get("userid")
		authtoken = self.request.get("authtoken")
		itemid = self.request.get("itemid")
		restaurantid = self.request.get("restaurantid")
		restaurantname = self.request.get("restaurantname")
		itemname = self.request.get("itemname")
		rating = self.request.get("rating")   #1 or 0
		description = self.request.get("description")
		latitude = self.request.get("latitude")
		longitude = self.request.get("longitude")
                input = self.request.get("input")
                input2 = self.request.get("input2")
                promptid = self.request.get("promptid")

		if restaurantid == "":
			restaurantid = None

		if itemid == "":
			itemid = None

		if description == "":
			description = None

		if rating == "100":
			rating = 100
		elif rating == "50":
			rating = 50
		elif rating == "0":
			rating = 0
                        
                if input == "":
                        input = None

                if input2 == "":
                        input2 = None

                if promptid == "":
                        promptid = None
                        prompt = None
                else:
                        prompt = Prompt.get_by_id(int(promptid))

		#user = self.auth.get_user_by_token(int(userid), authtoken)
                user = auth.get_auth().get_user_by_token(int(userid), authtoken)

		if restaurantid:
			restaurant = Restaurant.get_by_id(int(restaurantid))
		else:
			restaurant = Restaurant(
				name = restaurantname
				)
			#locationstring = latitude + ", " + longitude
			#restaurant.updatelocation(locationstring)
			restaurant.location = db.GeoPt(latitude, longitude)
			restaurant.put()


		if itemid:
			item = Item.get_by_id(int(itemid))
		else:
			item = Item(
				name = itemname,
				restaurant = restaurant
				)
			item.put()
			restaurant.numberofitems += 1
			restaurant.put()
			
		review = Review.all().filter("userid =", int(userid)).filter("item =", item).get()

		if not review:
			review = Review(
				userid = int(userid),
				item = item,
				rating = int(rating),
				description = description,
                                input = input,
                                input2 = input2,
                                prompt = prompt
				)
			item.numberofreviews += 1
			item.put()
			restaurant.numberofreviews += 1
			restaurant.put()
		else:
			review.rating = int(rating)
			review.description = description
                        review.input = input
                        review.input2 = input2
                        review.prompt = prompt
		review.put()
		item.updateindex()
		restaurant.updateindex()
		values = {
			"response": 1,
			"rating": item.rating(),
			}
		renderjson(self, values)

class GetProfile(BaseHandler):
	def get(self):
		userid = self.request.get("userid")
		user = User.get_by_id(int(userif))
		lists = List.all().filter("userid =", userid).run()
		values = {
			"user": user,
			"lists": lists,
			}
		renderjson(self, values)
		#user = self.auth.get_user_by_token(int(userid), authtoken)

class CreateRestaurant(webapp2.RequestHandler):
#OLD
#given restaurantname, address, city, state, zipcode 
#return restaurant id
	def get(self):
		if self.request.get("name") == "":
			renderjson(self, "Error, supply a name in the request")
		restaurant = Restaurant(
			name = self.request.get("name"),
			address = self.request.get("address"),
			city = self.request.get("city"),
			zipcode = self.request.get("zipcode"),
			restaurant = restaurant,
			)
		
		restaurant.put()
		if restaurant.key():
			values = restaurant.key().id()
			renderjson(self, values)
		else:
			renderjson(self, "Error on save")

class CreateItem(webapp2.RequestHandler):
#OLD
#given restaurantid, name, description, price
#return item id
    def get(self):
	    restaurant = Restaurant.get_by_id(int(restaurantid))
	    item = Item(
		    name = self.request.get("name"),
		    description = self.request.get("description"),
		    price = self.request.get("price"),
		    restaurant = restaurant
		    )
	    item.put()
	    if item.key():
		    values = item.key().id()
		    renderjson(self, values)
	    else:
		    renderjson(self, "Error on item add")

class ListHandler(webapp2.RequestHandler):
	def get(self):
		listid = self.request.get("listid")
		thislist = List.get_by_id(int(listid))
		values = {
			"response": 1,
			"itemids": thislist.itemids,
			"list": thislist
			}
		renderjson(self, values)
		
	def post(self):
		userid = self.request.get("userid")
		authtoken = self.request.get("authtoken")

		user = User.get_by_id(int(userid))

		action = self.request.get("action")
		values = {
			response: 0
			}

		if action == "create":
			listname = self.request.get("listname")
			thislist = List(
				userid = int(userid),
				name = listname,
				)
			thislist.put()
			values = {
				response: 1,
				listid: thislist.key().id(),
				}

		elif action == "delete":
			listid = self.request.get("listid")
			thislist = List.get_by_id(int(listid))
			thislist.delete()
			values['response'] = 1

		elif action == "rename":
			listid = self.request.get("listid")
			listname = self.request.get("listname")
			thislist = List.get_by_id(int(listid))
			thislist.name = listname
			thislist.put()
			values['response'] = 1

		elif action == "follow":
			listid = self.request.get("listid")
			thislist = List.get_by_id(int(listid))
			thislist.followerids.append(userid)
			thislist.put()
			values['response'] = 1

		elif action == "unfollow":
			listid = self.request.get("listid")
			thislist = List.get_by_id(int(listid))
			try: thislist.followerids.remove(userid)
			except: pass
			thislist.put()
			values['response'] = 1

		elif action == "additem":
			listid = self.request.get("listid")
			thislist = List.get_by_id(int(listid))
			itemid = self.requset.get("itemid")
			thislist.itemids.append(itemid)
			thislist.put()
			values['response'] = 1

		elif action == "removeitem":
			listid = self.request.get("listid")
			thislist = List.get_by_id(int(listid))
			itemid = self.requset.get("itemid")
			thislist.itemids.remove(itemid)
			thislist.put()
			values['response'] = 1

		renderjson(self,values)

#    ('/json/getfeed', GetFeed),
class GetFeed(webapp2.RequestHandler):
        def get(self):
                self.response.headers['Access-Control-Allow-Origin'] = '*'
		userid = self.request.get("userid")
		authtoken = self.request.get("authtoken")
                user = User.get_by_id(int(userid))

                values = {}
                feed_items = []
                
                for review in Review.all().filter("userid IN", user.following).order("date_edited").run():
                        try: prompt = review.prompt.name
                        except: prompt = None
                        reviewuser = User.get_by_id(int(review.userid))
                        review = {
                                "username": reviewuser.auth_ids[0],
                                "userid": review.userid,
                                "useremail": reviewuser.email_address,
                                "reviewid": review.key().id(),
                                "item": review.item.name,
                                "description": review.description,
                                "itemid": review.item.key().id(),
                                "rating": review.rating,
                                "restaurant": review.item.restaurant.name,
                                "restaurantid": review.item.restaurant.key().id(),
                                "prompt": prompt,
                                "input": review.input,
                                "input2": review.input2
                        }
                        feed_items.append(review)

                values['response'] = 1
                values['feed_items'] = feed_items

                renderjson(self,values)

#    ('/json/follow', FollowUser),
class FollowUser(BaseHandler):
        def get(self):
                pass

#     ('/json/getprompt', GetPrompt),
class GetPrompt(BaseHandler):
        def get(self):
                values = {}
                promptkey = random.choice([key for key in Prompt.all(keys_only=True).run()])
                prompt = Prompt.get(promptkey)

                values['response'] = 1
                values['prompt'] = prompt.name
                values['promptid'] = prompt.key().id()

                renderjson(self,values)
                

class Test(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Success")
    def post(self):
	    values = {
		    "success": 1
		    }
	    renderjson(self, values)
