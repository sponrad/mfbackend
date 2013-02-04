import webapp2
from models import *
from geo import geotypes
import helpers, globs

templatepath = '_templates/'

#render(self, 'account.html', values)
def render(self, t, values):
    values['URLS'] = URLS
    try: values['referer'] = self.request.headers['Referer']
    except: values['referer'] = "/"
    values['account'] = Account.all().filter("user =", values['user']).get()
    templatefile = URLS['templates'] + t
    path = os.path.join(os.path.dirname(__file__), templatefile)
    self.response.out.write(template.render(path, values))

