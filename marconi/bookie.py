from tools import getMongoDb, time, UTCstr2epoch, logging, pymongo

logger = logging.getLogger(__name__)


class Bookie(object):

    def __init__(self, api, market):
        self.api = api
        self.market = market
        self.db = getMongoDb('poloniex', 'my%sTradeHistory' % market)
        self.updateTradeHist()

    def myTradeHistory(self, query=None):
        return list(self.db.find(query))

    def updateMyTradeHist(self):
        try:
            old = list(self.db.find().sort('timestamp', pymongo.ASCENDING))[-1]
        except IndexError:
            logger.warning('No trades found in database')
            old = {'timestamp': time() - self.api.YEAR * 10}
        start = old['timestamp'] + 1
        hist = self.api.returnTradeHistory(self.market, start=start)
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
                self.db.update_one({"_id": _id}, {"$set": trade}, upsert=True)


if __name__ == '__main__':
    from tools import Poloniex
    from sys import argv
    logging.basicConfig(level=logging.INFO)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    bookie = Bookie(api, 'BTC_DOGE')
    print(bookie.myTradeHistory()[0])
