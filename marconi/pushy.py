from tools import Application
from tools import html, getMongoDb, summarize_blocks, sleep, logging
from tools import BL, GR
from tools.poloniex import Poloniex
from collections import deque

logger = logging.getLogger(__name__)


class Pushy(Application):

    def populateTicker(self):
        initTick = self.api.returnTicker()
        for market in initTick:
            initTick[market]['_id'] = market
            self.tickDb.update_one(
                {'_id': market},
                {'$set': initTick[market]},
                upsert=True)
        logger.info('Populated markets database with ticker data')

    async def onTick(self, **kwargs):
        self.tickDb.update_one(
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

    async def onTroll(self, **kwargs):
        kwargs['_id'] = kwargs.pop("id")
        name = kwargs["username"]
        rep = kwargs["reputation"]
        message = kwargs['message'] = html.unescape(kwargs.pop("text"))
        logger.debug('%s(%s): %s', BL(name), GR(str(rep)), message)
        self.tollbox.append(message)
        if time() - self.summaryTime > self.api.HOUR:
            self.summaryTime = time()
            self.trollDb.insert_one({
                '_id': self.summaryTime,
                'summary': summarize_blocks(self.trollbox)
            })

    async def main(self):
        self.tollbox = deque(list(), 200)
        self.api = Poloniex(jsonNums=float)
        self.tickDb = getMongoDb('markets')
        self.trollDb = getMongoDb('trollbox')
        self.summaryTime = self.trollDb.find_one()
        if not self.summaryTime:
            self.summaryTime = time()
            self.trollDb.drop()
        else:
            self.summaryTime = self.summaryTime['_id']
        self.populateTicker()
        self.push.subscribe(topic="trollbox", handler=self.onTroll)
        self.push.subscribe(topic="ticker", handler=self.onTick)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = Pushy()
    app.run()
    while True:
        try:
            sleep(1)
        except:
            app.stop()
