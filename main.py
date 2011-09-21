from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.api import xmpp
from google.appengine.api import mail
import logging
import cgi, os, urllib

import quote

class Alert(db.Model):
  ticker     = db.StringProperty()
  hi_price   = db.FloatProperty()
  low_price  = db.FloatProperty()
  user       = db.UserProperty()
  curr_price = db.FloatProperty()

class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    path = os.path.join(os.path.dirname(__file__), 'set_alerts.html')
    query = Alert.all().filter('user = ', user)
    template_values = {
      'alerts': query.fetch(1000),
      'user' : user,
    }
    self.response.out.write(template.render(path, template_values))

class DeleteAlert(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    
    user = users.get_current_user()

    if not user:
      self.response.out.write("no user found, redirecting to login...")
      self.redirect(users.create_login_url(self.request.uri))
    else:
      ticker = urllib.unquote( cgi.escape(self.request.get('ticker')).upper() )
      
      query = Alert.all()
      query.filter('user = '  , user)
      query.filter('ticker = ', ticker)
      
      alerts = query.fetch(1000)
      
      for alert in alerts:
        alert.delete()
    

class CheckAlerts(webapp.RequestHandler):
  def get(self):
    query = Alert.all()
    offset = 0
    alerts = query.fetch(1000)
    
    if not alerts:
      self.response.out.write("No Tickers...") 
      return
    
    users   = {}
    tickers = set()
    
    for alert in alerts:
      user   = alert.user
      ticker = alert.ticker.upper()
      
      if user in users:
        users[user].append(alert)
      else:
        users[user] = [alert]
      
      tickers.add(ticker)
    
    l = list(tickers)
    
    q = quote.quote()
    for i in range(0,len(tickers),5):
      d = q.get_quote(l[i:i+5])
      
      prices = self.getData(d)
      
      for user, alerts in users.items():
        for alert in alerts:
          hi_price  = float(alert.hi_price)
          low_price = float(alert.low_price)
          ticker    = alert.ticker.upper()
          
          if ticker not in l[i:i+5]:
            continue
          
          user_address = user.email()
          price = prices[ticker]
          
          if price > hi_price:
            self.response.out.write("Broke above %s's limit of $%.2f for %s, now at %.2f" % (user.nickname(),hi_price,ticker, price) )
            
            chat_message_sent = False
            msg = "%s went up to %.2f (Which is past your limit of %.2f)!" % (ticker,price,hi_price)
            status_code = xmpp.send_message(user_address, msg)
            chat_message_sent = (status_code == xmpp.NO_ERROR)
            
            if mail.is_email_valid(user_address):
              sender_address = "rpibic@gmail.com"
              subject = "Alert for %s" % (ticker)
              body = "Broke above %s's limit of $%.2f for %s, now at %.2f" % (user.nickname(),hi_price,ticker,price)
              
              mail.send_mail(sender_address, user_address, subject, body)
              
            alert.delete()
            
          elif price < low_price:
            self.response.out.write("Broke below %s's limit of $%.2f for %s, now at %.2f" % (user.nickname(),low_price,ticker,price) )
            
            chat_message_sent = False
            msg = "%s went down to %.2f (Which is past your limit of %.2f)!" % (ticker,price,low_price)
            status_code = xmpp.send_message(user_address, msg)
            chat_message_sent = (status_code == xmpp.NO_ERROR)
            
            
            if mail.is_email_valid(user_address):
              sender_address = "rpibic@gmail.com"
              subject = "Alert for %s" % (ticker)
              body = "Broke below %s's limit of $%.2f for %s, now at %.2f" % (user.nickname(),low_price,ticker,price)
              
              mail.send_mail(sender_address, user_address, subject, body)
              
            alert.delete()
          else:
            alert.curr_price = prices[ticker]
            alert.put()
  
  def getData(self,stocks):
    d = {}
    if isinstance(stocks, list):
      for stock in stocks:
        if stock['unknownsymbol'] == 'false':
          continue
        d[(stock['instrument']['sym']).upper()] = float(stock['quote']['lastprice'])
      return d
    else:
        if stocks['unknownsymbol'] == 'false':
          continue
      d[(stocks['instrument']['sym']).upper()] = float(stocks['quote']['lastprice'])
      return d
    
class AddAlert(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    
    user = users.get_current_user()

    if not user:
      self.response.out.write("no user found, redirecting to login...")
      self.redirect(users.create_login_url(self.request.uri))
    else:
      ticker    = urllib.unquote( cgi.escape(self.request.get('ticker'   )).upper() )
      hi_price  = urllib.unquote( cgi.escape(self.request.get('hi_price' )).lower() )
      low_price = urllib.unquote( cgi.escape(self.request.get('low_price')).lower() )
      
      if not hi_price:
        hi_price = 1000
      if not low_price:
        low_price = 0
      
      query = Alert.all()
      query.filter('user = '  , user)
      query.filter('ticker = ', ticker)
      
      prev_alerts = query.fetch(1)
      
      if prev_alerts:
        prev_alert = prev_alerts[0]
        
        prev_alert.hi_price  = float(hi_price)
        prev_alert.low_price = float(low_price)
        prev_alert.put()
      else:
        alert = Alert()
        
        alert.ticker    = ticker
        alert.hi_price  = float(hi_price)
        alert.low_price = float(low_price)
        alert.user      = user
        
        alert.put()

application = webapp.WSGIApplication(
  [('/check_alerts', CheckAlerts),
   ('/add_alert', AddAlert),
   ('/delete_alert', DeleteAlert),
   ('/', MainPage),])
   
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
