from unicodedata import category

from pybit.unified_trading import HTTP

cl = HTTP()

r = cl.get_orderbook(category="linear", symbol = "BTCUSDT")

print(r)


