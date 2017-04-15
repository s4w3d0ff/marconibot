from tools import itemgetter, logging, MongoClient, time
from chart import Chart

logger = logging.getLogger(__name__)


class Market(object):
    """ Holds data for a market <pair> """

    def __init__(self, pair, api, **kwargs):
        self.pair = pair.upper()
        self.api = api
        self._chart = Chart(self.pair, self.api, **kwargs)
        self.db = MongoClient().poloniex['markets']

    @property
    def chart(self):
        return self._chart()

    @property
    def balances(self):
        coins = self.pair.split('_')
        bals = self.api.returnCompleteBalances()
        return {coins[0]: bals[coins[0]], coins[1]: bals[coins[1]]}

    @property
    def openOrders(self):
        return self.api.returnOpenOrders(self.pair)

    @property
    def volume24h(self):
        try:  # look for old timestamp
            timestamp = self.db.find_one({
                '_id': self.pair})['volume24h']['timestamp']
        except Exception as e:  # not found
            logger.exception(e)
            timestamp = 0

        if time() - timestamp > 60 * 2:
            timestamp = time()
            vol = self.api.return24hVolume()[self.pair]
            vol['timestamp'] = timestamp
            self.db.update_one(
                {'_id': self.pair},
                {'$set': {'volume24h': vol}},
                upsert=True)
        return self.db.find_one({'_id': self.pair})['volume24h']

    @property
    def orderBook(self):
        try:  # look for old timestamp
            timestamp = self.db.find_one({
                '_id': self.pair})['orderbook']['timestamp']
        except Exception as e:  # not found
            logger.exception(e)
            timestamp = 0

        if time() - timestamp > 60 * 2:
            timestamp = time()
            book = self.api.returnOrderBook(self.pair, 50)
            book['timestamp'] = timestamp
            self.db.update_one(
                {'_id': self.pair},
                {'$set': {'orderbook': book}},
                upsert=True)
        return self.db.find_one({'_id': self.pair})['orderbook']

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
