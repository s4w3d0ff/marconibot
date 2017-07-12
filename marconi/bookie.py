from .tools import time, UTCstr2epoch, logging, pymongo

logger = logging.getLogger(__name__)


class Bookie(object):

    def __init__(self, api):
        self.api = api
        self.db = pymongo.MongoClient().poloniex

    def updateTradeHistory(self, market):
        try:
            old = list(self.db[market + 'tradeHistory'].find().sort(
                'timestamp', pymongo.ASCENDING))[-1]
        except:
            logger.warning('No %s trades found in database', market)
            old = {'timestamp': time() - self.api.YEAR * 10}
        start = old['timestamp'] + 1
        hist = self.api.returnTradeHistory(market, start=start)
        if len(hist) > 0:
            logger.info('%d new trade database entries' % len(hist))

            for trade in hist:
                _id = trade['globalTradeID']
                del trade['globalTradeID']
                trade['timestamp'] = UTCstr2epoch(trade['date'])
                trade['amount'] = float(trade['amount'])
                trade['total'] = float(trade['total'])
                trade['tradeID'] = int(trade['tradeID'])
                trade['orderNumber'] = int(trade['orderNumber'])
                trade['rate'] = float(trade['rate'])
                trade['fee'] = float(trade['fee'])
                self.db[market + 'tradeHistory'].update_one(
                    {"_id": _id}, {"$set": trade}, upsert=True)

    def myTradeHistory(self, market, query=None):
        self.updateTradeHistory(market)
        return list(self.db[market + 'tradeHistory'].find(query).sort(
            'timestamp', pymongo.ASCENDING))

if __name__ == '__main__':
    from .tools import Poloniex
    from sys import argv
    from pprint import pprint
    logging.basicConfig(level=logging.INFO)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    bookie = Bookie(api)
    pprint(bookie.myTradeHistory('BTC_DASH')[-6:])
