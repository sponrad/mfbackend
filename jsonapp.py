import webapp2
from mfb.jsonhandlers import *

config = {
    'webapp2_extras.auth': {
        'user_model': 'mfb.models.User',
        'user_attributes': ['auth_ids', 'admin'],
        },
    'webapp2_extras.sessions': {
        'secret_key': 'THISKEYISSUCHASECRET',
        }
    }

app = webapp2.WSGIApplication([
    ('/json/items', GetItems),
    ('/json/restaurants', GetRestaurants),
    ('/json/getrestaurants', GetRestaurantsGoogle),
    ('/json/getmenu', GetMenu),         #restaurantid
    ('/json/getitem', GetItem),         #
    ('/json/profile', GetProfile),
    ('/json/getitemsuggestions', GetItemSuggestions),
    ('/json/getrestaurantsuggestions', GetRestaurantSuggestions),
    ('/json/getrestaurantid', GetRestaurantId),
    ('/json/getprompt', GetPrompt),

    ('/json/getprofile', GetProfile),

    ('/json/reviewitem', ReviewItem),   #userid, authtoken, itemid, rating, description
    ('/json/getitemreviews', GetItemReviews),
    ('/json/createrestaurant', CreateRestaurant),
    ('/json/createitem', CreateItem),

    ('/json/list', ListHandler), #create/delete, (un)follow, add/remove item
    ('/json/getfeed', GetFeed),
    ('/json/loadmorefeed', LoadMoreFeed),
    ('/json/followuser', FollowUser),
    ('/json/unfollowuser', UnFollowUser),
    ('/json/signup', Signup),
    ('/json/login', Login),
    ('/json/logout', Logout),
    ('/json/', Test),
    ('/json', Test),
], debug=True, config=config)
