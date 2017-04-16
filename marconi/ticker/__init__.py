# -*- coding: utf-8 -*-
# 3rd party
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
# local
from tools import MongoClient, Process, logging
from market import Market

logger = logging.getLogger(__name__)


class WAMPTicker(ApplicationSession):
    """ WAMP application - subscribes to the 'ticker' push api and saves pushed
    data into a mongodb """
    @inlineCallbacks
    def onJoin(self, details):
        # open/create poloniex database, ticker collection/table
        self.db = MongoClient().poloniex['markets']
        yield self.subscribe(self.onTick, 'ticker')
        logger.info('Subscribed PushApi Ticker')

    def onTick(self, *data):
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
        # thread namespace
        self._appProcess = None
        self._appRunner = ApplicationRunner(
            u"wss://api.poloniex.com:443", u"realm1"
        )
        self.markets = {}

    def __call__(self, market):
        """ returns ticker from mongodb """
        if market not in self.markets:
            self.markets[market] = Market(market, self.api)
        return self.markets[market]()

    def chart(self, market):
        if market not in self.markets:
            self.markets[market] = Market(market, self.api)
        return self.markets[market].chart()

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
