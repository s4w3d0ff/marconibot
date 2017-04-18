from tools.minion import Minion
from tools import MongoClient


class OrderBookie(Minion):
    self.db = MongoClient().poloniex['markets']

    def run(self):

    def getTimestamp(self, name):
        try:  # look for old timestamp
            timestamp = self.db.find_one({'_id': 'timestamps'})[name]
            logger.debug('%s last updated %f', name, timestamp)
        except:  # not found
            logger.debug('No timestamp found for %s', name)
            timestamp = 0
        return timestamp

    def setTimestamp(self, name):
        self.db.update_one(
            {'_id': 'timestamps'},
            {'$set': {name: time()}},
            upsert=True)
        logger.debug('%s timestamp updated', name)

    def update24hVol(self):
        if time() - self.getTimestamp('volume24h') > 60 * 2:  # 2 min
            vols = self.api.return24hVolume()
            for market in vols:
                self.db.update_one(
                    {'_id': market},
                    {'$set': {'volume24h': vols[market]}},
                    upsert=True)
            self.setTimestamp('volume24h')
            logger.info('Updated volume24h')

    def updateOrderBook(self):
        if time() - self.getTimestamp('orderbook') > 5:  # 5 sec
            book = self.api.returnOrderBook(depth=30)
            for market in book:
                self.db.update_one(
                    {'_id': market},
                    {'$set': {'orderbook': book[market]}},
                    upsert=True)
            self.setTimestamp('orderbook')
            logger.info('Updated orderbook')
