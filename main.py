import webapp2
import mfb.admin as admin
import mfb.handlers as main

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
    ('/_a/restaurants', admin.Restaurants),
    (r'/_a/restaurant/(.*)', admin.RestaurantPage),
    ('/_a/cards', admin.Cards),
    ('/_a/prompts', admin.Prompts),
    ('/_a/hand', admin.CardHand),
    ('/_a/itemvote', admin.ItemVote),
    ('/_a/signup', admin.SignupHandler),
    ('/_a/login', admin.LoginHandler),
    ('/_a/logout', admin.LogoutHandler),
    ('/_a/editable', admin.Editable),
    ('/_a/ajax', admin.AjaxHandler),
    ('/_a/delete', admin.Delete),
    ('/_a/password', admin.Password),
    ('/_a/maintain', admin.Maintain),
    webapp2.Route('/_a', admin.MainHandler, name="home"),

    ('/signup', main.SignupHandler),
    ('/login', main.LoginHandler),
    ('/logout', main.LogoutHandler),
    ('/restaurants', main.Restaurants),    
    ('/items/(.*)', main.Items),
    ('/items', main.Items),
    ('/vote/(.*)', main.Vote),
    ('/votenew/(.*)', main.VoteNew),
    ('/feed', main.Feed),
    ('/find', main.FindPeople),
    ('/review/(.*)', main.ReviewPage), 
    ('/profile/(.*)/followers', main.Followers), 
    ('/profile/(.*)/following', main.Following), 
    ('/profile/(.*)', main.Profile), #profile?profileid
     
    ('/', main.MainHandler),
], debug=True, config=config)
