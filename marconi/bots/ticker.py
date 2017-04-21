#!/usr/bin/python
# -*- coding: utf-8 -*-

from tools import (inlineCallbacks, ApplicationSession, ApplicationRunner,
                   reactor, MongoClient, Process, time, logging)

logger = logging.getLogger(__name__)


class WAMPTicker(ApplicationSession):
    """ WAMP application - subscribes to the 'ticker' push api and saves pushed
    data into a mongodb"""

    @inlineCallbacks
    def onJoin(self, details):
        # open/create poloniex database, ticker collection/table
        self.db = MongoClient().poloniex['markets']
        yield self.subscribe(self.onTick, 'ticker')
        logger.info('Subscribed to PushApi Ticker')

    def onTick(self, *data):
        """ 'upserts' data into 'markets' collection"""
        self.db.update_one(
            {"_id": data[0]},
            {"$set": {'last': data[1],
                      'lowestAsk': data[2],
                      'highestBid': data[3],
                      'percentChange': data[4],
                      'baseVolume': data[5],
                      'quoteVolume': data[6],
                      'isFrozen': data[7],
                      '24hrHigh': data[8],
                      '24hrLow': data[9]
                      }},
            upsert=True)

    def onDisconnect(self):
        # stop reactor if disconnected
        if reactor.running:
            reactor.stop()


class Ticker(object):

    def __init__(self, api):
        self._running = False
        # open/create poloniex database, ticker collection/table
        self.db = MongoClient().poloniex['markets']
        self.api = api
        # populate db
        self.populateTicker()
        # thread namespace
        self._appProcess = None
        self._appRunner = ApplicationRunner(
            u"wss://api.poloniex.com:443", u"realm1"
        )

    def __call__(self, market):
        """ returns ticker from mongodb """
        return self.db.find_one({'_id': market})

    def populateTicker(self):
        initTick = self.api.returnTicker()
        for market in initTick:
            initTick[market]['_id'] = market
            self.db.update_one(
                {'_id': market},
                {'$set': initTick[market]},
                upsert=True)
        logger.info('Populated markets database with ticker data')

    def start(self):
        """ Start WAMP application runner process """
        self._appProcess = Process(
            target=self._appRunner.run, args=(WAMPTicker,)
        )
        self._appProcess.daemon = True
        self._appProcess.start()
        self._running = True

    def stop(self):
        """ Stop WAMP application """
        try:
            self._appProcess.terminate()
        except:
            pass
        try:
            self._appProcess.join()
        except:
            pass
        self._running = False

if __name__ == '__main__':
    from tools import sleep, Poloniex
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    ticker = Ticker(Poloniex(jsonNums=float))
    ticker.start()
    while ticker._running:
        try:
            logging.info('USDT_BTC last: %s' % ticker('USDT_BTC')['last'])
            sleep(10)
        except Exception as e:
            logging.exception(e)
            ticker.stop()
