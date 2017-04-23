from tools.minion import Minion
from tools import satoshi, tradeMin, sleep, roundDown, logging

logger = logging.getLogger(__name__)


class FrontRunner(Minion):

    def __init__(self, api, market, allowance=0.01):
        self.api, self.market = api, market
        self.allowance = allowance
        self.parentCoin, self.childCoin = self.market.split('_')
        self.orderNumber, self.buyPrice, self.sellPrice = None, None, None

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

    def getCoinBal(self, coin):
        bals = self.api.returnAvailableAccountBalances('exchange')[
            'exchange']
        logger.debug(bals)
        if not coin in bals:
            return 0.0
        return float(bals[coin])

    def wait(self):
        logger.debug('Waiting 10 sec...')
        sleep(10)

    def frontSell(self):
        """ Creates a sell order for self.market using all coins in balance and
        the 'front' of market as the ask rate. Keeps pushing the order to
        'front' until the order is filled. """
        # amount is all available 'child' coins
        amount = self.getCoinBal(self.childCoin)
        if amount < tradeMin:
            return logger.error('Available %s amount is below tradeMin: %s.',
                                self.childCoin, str(tradeMin))
            # get 'front'
        self.sellPrice = self.getFront('sell')
        # create sell order
        orderNumber = int(self.api.sell(
            self.market,
            self.sellPrice,
            amount,
            orderType='postOnly')['orderNumber'])
        logger.debug('ordernumber: %s', str(orderNumber))
        # wait for order to close
        while 1:
            # is our order still open?
            for order in self.api.returnOpenOrders(self.market):
                # not our order? skip it...
                if int(order['orderNumber']) != int(orderNumber):
                    continue
                # this should be our order
                logger.debug(order)
                # order is still active, get current 'front'
                front = self.getFront('sell')
                # if order is behind front
                logger.debug('front: %s', str(front))
                if float(order['rate']) > front:
                    logger.info('Moving order %s to "front"',
                                str(orderNumber))
                    self.sellPrice = front
                    # move order to front
                    norder = self.api.moveOrder(
                        orderNumber, self.sellPrice, orderType='postOnly')
                    if 'success' in norder and int(norder['success']) == 1:
                        # update orderNumber
                        orderNumber = int(norder['orderNumber'])
                        logger.debug('ordernumber: %s', str(orderNumber))
                    else:
                        logger.error(norder)
                        break
                self.wait()
                break  # break for loop we found our order
            else:
                # order wasn't found in openOrders (it closed?)
                return self.sellPrice, orderNumber

    def frontBuy(self):
        """ Creates a buy order for self.market using self.allowance as the
        amount and the 'front' of market as the bid rate. Keeps pushing the
        order to 'front' until the order is filled. """
        # don't make order if we don't have the avail funds
        if self.getCoinBal(self.parentCoin) < self.allowance:
            return logger.error(
                '%s amount is below %s', self.parentCoin, str(self.allowance))
        # get 'front'
        self.buyPrice = self.getFront('buy')
        amount = roundDown(self.allowance / price)
        # create buy order
        orderNumber = int(
            self.api.buy(self.market, self.buyPrice, amount,
                         orderType='postOnly')['orderNumber'])
        logger.debug('ordernumber: %s', str(orderNumber))
        # wait for order to close
        while 1:
            # is our order still open?
            for order in self.api.returnOpenOrders(self.market):
                # not our order? skip it...
                if int(order['orderNumber']) != int(orderNumber):
                    continue
                # this should be our order
                logger.debug(order)
                # order is still active, get current 'front'
                front = self.getFront('buy')
                # if order is behind front
                logger.debug('front: %s', str(front))
                if float(order['rate']) < front:
                    logger.info('Moving order %s to "front"',
                                str(orderNumber))
                    self.buyPrice = front
                    # move order to front
                    norder = self.api.moveOrder(
                        orderNumber, self.buyPrice, orderType='postOnly')
                    if 'success' in norder and int(norder['success']) == 1:
                        # update orderNumber
                        orderNumber = int(norder['orderNumber'])
                        logger.debug('ordernumber: %s', str(orderNumber))
                    else:
                        # break 'for loop', error
                        logger.error(norder)
                        break
                # our order is still open
                # wait and check again
                self.wait()
                break
            else:
                # order wasn't found in openOrders (it closed?)
                return self.buyPrice, orderNumber


if __name__ == '__main__':
    from tools import Poloniex
    from sys import argv
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    trader = FrontRunner(api, False, 'BTC_BTM')
    print(trader.frontBuy())
