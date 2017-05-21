from tools import Application
from tools import html, getMongoDb, sleep, time, logging
from tools import BL, GR
from tools.poloniex import Poloniex
from tools.summarize import summarize_blocks
from collections import deque


logger = logging.getLogger(__name__)


class Pushy(Application):
    trollbox = deque(list(), 100)

    def populateTicker(self):
        initTick = self.api.returnTicker()
        for market in initTick:
            initTick[market]['_id'] = market
            self.tickDb.update_one(
                {'_id': market},
                {'$set': initTick[market]},
                upsert=True)
        logger.info('Populated markets database with ticker data')

    def onTick(self, **kwargs):
        if kwargs['currency_pair'] == 'USDT_BTC':
            logger.debug(
                '%s: Last:%s lAsk:%s hBid:%s',
                str(kwargs["currency_pair"]),
                str(kwargs["last"]),
                str(kwargs["lowest_ask"]),
                str(kwargs["highest_bid"]))
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

    def onTroll(self, **kwargs):
        name = kwargs["username"]
        rep = kwargs["reputation"]
        message = html.unescape(kwargs["text"])
        logger.debug('%s(%s): %s', BL(name), GR(str(rep)), message)
        self.trollbox.append(message)
        if time() - self.summaryTime > self.api.MINUTE * 5:
            self.summaryTime = time()
            summary = summarize_blocks(self.trollbox)
            logger.info(summary)
            self.trollDb.insert_one({
                '_id': self.summaryTime,
                'summary': summarize_blocks(self.trollbox)
            })

    async def main(self):
        self.api = Poloniex(jsonNums=float)
        self.tickDb = getMongoDb('markets')
        #self.trollDb = getMongoDb('trollbox')
        #self.summaryTime = self.trollDb.find_one()
        # if not self.summaryTime:
        #    logger.info('No summary found.')
        #    self.summaryTime = time()
        # else:
        #    logger.info(self.summaryTime['summary'])
        #    self.summaryTime = self.summaryTime['_id']
        #    logger.info('Last summary time: %s', str(self.summaryTime))
        self.populateTicker()
        #self.push.subscribe(topic="trollbox", handler=self.onTroll)
        self.push.subscribe(topic="ticker", handler=self.onTick)
        logger.info('Subscribed to ticker')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('tools.poloniex').setLevel(logging.INFO)
    app = Pushy()
    app.run()
