import quote
import pprint
q = quote.quote()
pprint.pprint(q.get_quote(["AAPL","AMZN","GOOG","V","MCD","ALXN","YHOO","MSFT","PWE","GLD"]))