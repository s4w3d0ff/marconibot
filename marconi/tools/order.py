from . import logging, PoloniexError

logger = logging.getLogger(__name__)


class Order(object):

    def __init__(self, api, pair, orderNumber):
        self.api = api
        self.pair = pair
        self.orderNumber = int(orderNum)
        self.parentCoin, self.childCoin = self.pair.split('_')

    @property
    def trades(self):
        logger.info('Checking %s for trades', str(self.orderNumber))
        try:
            return self.api.returnOrderTrades(self.orderNumber)
            # {
            #   u'fee': u'0.00250000', u'tradeID': 1340160.0,
            #   u'rate': u'0.00000049', u'amount': u'145416.65021235',
            #   u'currencyPair': u'BTC_DOGE', u'date': u'2017-04-27 20:05:54',
            #   u'total': u'0.07125415', u'type': u'sell',
            #   u'globalTradeID': 113320231.0
            # }
        except PoloniexError:
            return False

    @property
    def order(self):
        logger.info('Checking open orders for %s', str(self.orderNumber))
        # check open orders for our order number
        openOrders = self.api.returnOpenOrders(self.pair)
        logger.debug(openOrders)
        for order in openOrders:
            # {u'orderNumber': u'12673776704',
            #   u'margin': 0.0,
            #   u'amount': u'2396.22536189',
            #   u'rate': u'0.00009000',
            #   u'date': u'2017-04-25 03:56:00',
            #   u'total': u'0.21566028',
            #   u'type': u'sell',
            #   u'startingAmount': u'2396.22536189'}
            if int(order['orderNumber']) == self.orderNumber:
                # we found the order (its still open)
                logging.info('Order is still open')
                return order
        else:
            return False
