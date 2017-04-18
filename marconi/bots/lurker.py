#!/usr/bin/python
# -*- coding: utf-8 -*-
# local
from tools import (inlineCallbacks, ApplicationSession, ApplicationRunner,
                   HTMLParser, MongoClient, time, sleep, Process, logging)

logger = logging.getLogger(__name__)


MODS = {"Xoblort": 1,
        "Chickenliver": 1,
        "MobyDick": 1,
        "cybiko123": 1,
        "SweetJohnDee": 1,
        "smallbit": 1,
        "Wizwa": 1,
        "OldManKidd": 1,
        "Quantum": 1,
        "busoni@poloniex": 1,
        "Thoth": 1,
        "wausboot": 1,
        "Mirai": 1,
        "qubix": 1,
        "Oldgamejunk": 1,
        "Chewpacabra": 1,
        "j33hopper": 1,
        "VenomGhost": 1,
        "ultim8um": 1,
        "TheDjentleman": 1,
        "Bigolas": 1,
        "Watchtower": 1}


NAME = 'PulloutKing'

html = HTMLParser()


class WAMPTrollbox(ApplicationSession):

    @inlineCallbacks
    def onJoin(self, details):
        global mods, name, html
        # load db
        self.db = MongoClient().poloniex['trollcard']
        yield self.subscribe(self.onTroll, 'trollbox')

    def checkMessage(self, coin, message):
        # TODO: use REGEX!!!!
        name = self.coins[coin]['name']
        if '%s ' % coin.lower() in message or '%s ' % coin in message:
            return True
        if '%s ' % name.lower() in message or '%s ' % name.upper() in message:
            return True
        if name in message:
            return True
        return False

    def onTroll(self, *args):
        try:
            # type, messageNumber, username, message, reputation
            mType, mNum, name, message, rep = args
            message = html.unescape(message)
            logger.info('%s(%s): %s', name, str(rep), message)
            for coin in self.coins:
                if int(self.coins[coin]['delisted']):
                    continue
                if self.checkMessage(coin, ' ' + message + ' '):

                    self.db.update_one({"_id": coin},
                                       {"$setOnInsert": {"count": 0}},
                                       upsert=True)
                    self.db.update_one({"_id": coin}, {"$inc": {"count": 1}})

        except ValueError:  # Sometimes its a banhammer! (only 4)
            mType, mNum, name, message = args
            logger.info('%s: %s', name, message)


class Lurker(object):
    """ Watches the trollbox, gives each coin a score depending on metions """

    def __init__(self, api):
        self.api = api
        self.db = MongoClient().poloniex['trollcard']
        self.app = WAMPTrollbox
        self.app.coins = self.api.returnCurrencies()
        self._running = False
        self._process = None
        self._appRunner = ApplicationRunner(u"wss://api.poloniex.com:443",
                                            u"realm1")

    def __call__(self, coin=False):
        """ Get current scorecard """
        if not coin:
            return [doc for doc in self.db.find()]
        return self.db.find_one({'_id': coin})

    def start(self):
        """ Begin trolling """
        self._process = Process(target=self._appRunner.run,
                                args=(WAMPTrollbox,))
        self._process.daemon = True
        self._running = True
        self._process.start()

    def stop(self):
        """ Stop trolling """
        try:
            self._process.terminate()
        except:
            pass
        try:
            self._process.join()
        except:
            pass
        self._running = False

if __name__ == "__main__":
    from tools import Poloniex
    logging.basicConfig(format='[%(asctime)s]%(message)s',
                        datefmt="%H:%M:%0S", level=logging.INFO)
    troll = Lurker(Poloniex())
    troll.start()
    while 1:
        try:
            sleep(1)
        except:
            troll.stop()
            break
    print(troll())
