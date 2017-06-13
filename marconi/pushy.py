from tools import Application
from tools import getMongoDb, sleep, time, logging
from tools import BL, GR
from tools.poloniex import Poloniex


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

    async def main(self):
        self.api = Poloniex(jsonNums=float)
        self.tickDb = getMongoDb('markets')
        self.populateTicker()
        self.push.subscribe(topic="ticker", handler=self.onTick)
        logger.info('Subscribed to ticker')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('tools.poloniex').setLevel(logging.INFO)
    app = Pushy()
    app.run()
