from tools.minion import Minion
from tools import satoshi, sleep, roundDown, logging

logger = logging.getLogger(__name__)


class FrontRunner(Minion):

    def __init__(self, api, ticker, market, allowance=0.01):
        self.api, self.ticker, self.market = api, ticker, market
        self.allowance = allowance
        self.orderNumber = None
        self.basePrice = None

    def getFront(self, arg):
        tick = self.api.returnTicker()[self.market]
        hbid = float(tick['highestBid'])
        lask = float(tick['lowestAsk'])
        if arg is 'buy':
            if hbid + satoshi == lask:
                return hbid
            else:
                return hbid + satoshi
        if arg is 'sell':
            if lask - satoshi == hbid:
                return lask
            else:
                return lask - satoshi

    def frontBuy(self):
        """ Creates a buy order for self.market using self.allowance as the
        amount and the 'front' of market as the bid rate. Keeps pushing the
        order the 'front' until the order is filled. """
        # get current avail bal
        exchangeBals = self.api.returnAvailableAccountBalances('exchange')[
            'exchange']
        logger.debug(exchangeBals)
        # don't make order if we don't have the avail funds
        if not 'BTC' in exchangeBals or float(exchangeBals['BTC']) < self.allowance:
            logger.error('Could not create buy order, not enough BTC')
            return None
        # get 'front'
        self.basePrice = self.getFront('buy')
        amount = roundDown(self.allowance / price)
        # create buy/sell order
        self.orderNumber = int(self.api.buy(
            self.market,
            price,
            amount,
            orderType='postOnly')['orderNumber'])
        logger.debug('ordernumber: %s', str(self.orderNumber))
        # wait for order to close
        while 1:
            logger.debug('Waiting 1 sec...')
            sleep(1)
            openOrders = self.api.returnOpenOrders(self.market)
            # is our order still open?
            for order in openOrders:
                # not our order? skip it...
                if int(order['orderNumber']) != int(self.orderNumber):
                    continue
                # this should be our order
                logger.debug(order)
                # order is still active, get current 'front'
                front = self.getFront('buy')
                # if order is behind front
                logger.debug('front: %s', str(front))
                if float(order['rate']) < front:
                    logger.info('Moving order %s to "front"',
                                str(self.orderNumber))
                    self.basePrice = front
                    # move order to front
                    norder = self.api.moveOrder(
                        self.orderNumber, self.basePrice, orderType='postOnly')
                    # update orderNumber (is this needed?)
                    self.orderNumber = int(norder['orderNumber'])
                    logger.debug('ordernumber: %s', str(self.orderNumber))
                break  # break for loop
            else:
                # order wasn't found in openOrders
                # we will assume the order was filled...
                return True

if __name__ == '__main__':
    from ticker import Ticker
    from tools import Poloniex, Decimal
    from sys import argv
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    trader = FrontRunner(api, False, 'BTC_BTM')
    print(trader.frontBuy())
