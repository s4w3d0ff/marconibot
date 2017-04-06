from . import itemgetter, logger
from .chart import Chart


class Market(object):
    """ Holds data for a market <pair> """

    def __init__(self, pair, **kwargs):
        self.pair = pair.upper()
        kwargs['pair'] = pair.upper()
        self.api = kwargs.get('api')
        self.chart = Chart(**kwargs)

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


if __name__ == '__main__':
    # python -m bots.tools.data
    from poloniex import Poloniex
    market = Market(pair="usdt_btc", api=Poloniex(jsonNums=float))
    print(market.chart())
