# -*- coding: utf-8 -*-
# local
from tools import (inlineCallbacks, ApplicationSession, ApplicationRunner,
                   reactor, MongoClient, Process, time, indica, logging, izip)

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
        self.update24hVol()
        self.updateOrderBook()

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

    def onDisconnect(self):
        # stop reactor if disconnected
        if reactor.running:
            reactor.stop()


class Ticker(object):

    def __init__(self, api, **kwargs):
        self._running = False
        # open/create poloniex database, ticker collection/table
        self.db = MongoClient().poloniex['markets']
        self.api = api
        # pass api to WAMP app
        self.app = WAMPTicker
        self.app.api = self.api
        # clear db (for development)
        self.db.drop()
        # populate db
        initTick = self.api.returnTicker()
        for market in initTick:
            initTick[market]['_id'] = market
            self.db.update_one(
                {'_id': market},
                {'$set': initTick[market]},
                upsert=True)
        # thread namespace
        self._appProcess = None
        self._appRunner = ApplicationRunner(
            u"wss://api.poloniex.com:443", u"realm1"
        )

    def __call__(self, market):
        """ returns ticker from mongodb """
        return self.db.find_one({'_id': market})

    def start(self):
        """ Start WAMP application runner process """
        self._appProcess = Process(
            target=self._appRunner.run, args=(self.app,)
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
