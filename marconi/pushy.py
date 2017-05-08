from tools import Application
from tools import HTMLParser, getMongoDb, sleep, logging

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


class Pushy(Application):

    def populateTicker(self):
        initTick = self.api.returnTicker()
        for market in initTick:
            initTick[market]['_id'] = market
            self.db.update_one(
                {'_id': market},
                {'$set': initTick[market]},
                upsert=True)
        self.logger.info('Populated markets database with ticker data')

    def onTick(self, **kwargs):
        self.db.update_one(
            {"_id": kwargs["currency_pair"]},
            {"$set": {'last': kwargs["last"],
                      'lowestAsk': kwargs["lowest_ask"],
                      'highestBid': kwargs["highest_bid"],
                      'percentChange': kwargs["percent_change"],
                      'baseVolume': kwargs["base_volume"],
                      'quoteVolume': kwargs["quote_volume"],
                      'isFrozen': kwargs["is_frozen"],
                      '24hrHigh': kwargs["day_high"],
                      '24hrLow': kwargs["day_low"]
                      }},
            upsert=True)

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

    def onTroll(self, **kwargs):

        mType = kwargs["type"]
        mNum = kwargs["id"]
        name = kwargs["username"]
        message = kwargs["text"]
        rep = kwargs["reputation"]
        message = html.unescape(message)
        self.logger.info('%s(%s): %s', name, str(rep), message)
        for coin in self.coins:
            if int(self.coins[coin]['delisted']):
                continue
            if self.checkMessage(coin, ' ' + message + ' '):
                self.db.update_one({"_id": coin},
                                   {"$setOnInsert": {"count": 0}},
                                   upsert=True)
                self.db.update_one({"_id": coin}, {"$inc": {"count": 1}})

    async def main(self):
        self.populateTicker()
        self.push.subscribe(topic="trollbox", handler=self.onTroll)
        self.push.subscribe(topic="ticker", handler=self.onTick)

if __name__ == '__main__':
    from tools.poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    app = Pushy()
    app.api = Poloniex(jsonNums=float)
    app.db = getMongoDb('markets')
    app.coins = app.api.returnCurrencies()
    app.run()
    while True:
        try:
            sleep(1)
        except:
            app.stop()
