from tools import itemgetter, logging
from chart import Chart

logger = logging.getLogger(__name__)


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

    @property
    def lowestask(self):
        return self.api.returnTicker()[self.pair]['lowestAsk']

    @property
    def highestbid(self):
        return self.api.returnTicker()[self.pair]['highestBid']

    @property
    def last(self):
        return self.api.returnTicker()[self.pair]['last']

    @property
    def percentChange(self):
        return self.api.returnTicker()[self.pair]['percentChange']

    @property
    def baseVolume(self):
        return self.api.returnTicker()[self.pair]['baseVolume']

    @property
    def quoteVolume(self):
        return self.api.returnTicker()[self.pair]['quoteVolume']

    @property
    def volume24(self):
        return self.api.return24hVolume()[self.pair]
