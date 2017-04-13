from tools import itemgetter, logging
from chart import Chart

logger = logging.getLogger(__name__)

"""
Markets Mongodb collection:
db = MongoClient().poloniex['markets']
{
    '_id': self.pair,
    'orderbook': self.api.returnOpenOrders(self.pair),
    '24Volume': self.api.return24Volume()[self.pair],
    'openOrders': self.api.returnOpenOrders(self.pair),
    'myBalances': self.balances,



}
"""


class Market(object):
    """ Holds data for a market <pair> """

    def __init__(self, pair, api, **kwargs):
        self.pair = pair.upper()
        kwargs['pair'] = pair.upper()
        self.api = api
        self.chart = Chart(self.pair, self.api, **kwargs)

    @property
    def balances(self):
        coins = self.pair.split('_')
        bals = self.api.returnCompleteBalances()
        return [bals[coins[0]], bals[coins[1]]]

    @property
    def openOrders(self):
        return self.api.returnOpenOrders(self.pair)

    @property
    def orderBook(self):
        return self.api.returnOrderBook(self.pair, 50)

    @property
    def sellwalls(self):
        book = self.orderBook['asks']
        book.sort(key=itemgetter(1), reverse=True)
        return book[:7]

    @property
    def buywalls(self):
        book = self.orderBook['bids']
        book.sort(key=itemgetter(1), reverse=True)
        return book[:7]
