import oauth2 as oauth
import time
from django.utils import simplejson as json
from keys import TradeKingKeys

class quote(object):
  def __init__(self):
    self.consumer_key = TradeKingKeys.consumer_key
    self.consumer_secret = TradeKingKeys.consumer_secret
    self.access_token = TradeKingKeys.access_token
    self.access_secret = TradeKingKeys.access_secret

  def get_quote(self, tickers):
    # Set the API endpoint 
    request_token_url = "https://api.tradeking.com/v1/market/quotes.json?delayed=false&symbols="
    request_token_url += ','.join(tickers)

    # Create the consumer with the proper key/secret.
    consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_secret)
    
    # Create the token
    token = oauth.Token(key=self.access_token, secret=self.access_secret)

    # Create our client.
    client = oauth.Client(consumer, token)

    # The OAuth Client request works just like httplib2 for the most part.
    resp, content = client.request(request_token_url, "GET")
    print json.loads(content)