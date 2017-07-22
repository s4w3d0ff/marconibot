from .. import logging, pd, np, time, SATOSHI, PoloniexError, TRADE_MIN

logger = logging.getLogger(__name__)


def cancelAllOrders(api, market='all', arg=False):
    """ Cancels all orders for a market or all markets. Can be limited to just
    buy or sell orders using the 'arg' param """

    orders = api.returnOpenOrders(market)

    if market == 'all':
        for market in orders:
            for order in orders[market]:
                if arg in ('sell', 'buy') and o['type'] != arg:
                    continue
                logger.debug(api.cancelOrder(order["orderNumber"]))
        return True

    for order in orders:
        if arg in ('sell', 'buy') and order['type'] != arg:
            continue
        logger.debug(api.cancelOrder(order["orderNumber"]))
    return True


def cancelAllLoanOffers(api, coin=False):
    """ Cancels all open loan offers, for all coins or a single <coin> """
    loanOrders = api.returnOpenLoanOffers()
    if not coin:
        for c in loanOrders:
            for order in loanOrders[c]:
                logger.info(api.cancelLoanOffer(order['id']))
    else:
        for order in loanOrders[coin]:
            logger.info(api.cancelLoanOffer(order['id']))


def closeAllMargins(api):
    """ Closes all margin positions """
    for m in api.returnTradableBalances():
        logger.info(api.closeMarginPosition(m))


def autoRenewAll(api, toggle=True):
    """ Turns auto-renew on or off for all active loans """
    if toggle:
        toggle = 1
    else:
        toggle = 0
    for loan in api.returnActiveLoans()['provided']:
        if int(loan['autoRenew']) != toggle:
            logger.info('Toggling autorenew for offer %s', loan['id'])
            api.toggleAutoRenew(loan['id'])


def frontSell(api, market, amount=False):
    """ Creates a sell order for <market> using all coins in balance at
    the 'front' of market. Keeps pushing the order to 'front' until the order
    is filled. """
    parentCoin, childCoin = market.split('_')
    if not amount:
        amount = getAvailCoin(api, childCoin)
    price = getFront(api, market, 'sell')
    if amount * sellPrice < TRADE_MIN:
        return 'Total %s is below TRADE_MIN: %s.' % (str(amount), str(TRADE_MIN))
    # create sell order
    initOrder = api.sell(market, price, amount, orderType='postOnly')
    orderNums = [int(initOrder['orderNumber'])]
    while 1:
        for order in api.returnOpenOrders(market):
            if int(order['orderNumber']) != int(orderNums[-1]):
                continue
            logger.debug(order)
            price = getFront(api, market, 'sell')
            if float(order['rate']) > price:
                logger.debug('Moving %s order %s', market, orderNums[-1])
                norder = api.moveOrder(
                    orderNums[-1], price, orderType='postOnly')
                if 'success' in norder and int(norder['success']) == 1:
                    orderNums.append(int(norder['orderNumber']))
                else:
                    logger.error(norder)
                    break
            wait()
            break
        else:
            return orderNums


def frontBuy(api, market, allowance=TRADE_MIN + SATOSHI):
    """ Creates a buy order for <market> using <allowance> as the
    amount and the 'front' of market as the bid rate. Keeps pushing the
    order to 'front' until the order is filled. returns a list of ordernumbers
    """
    logger.info('Creating "front buy" order in %s', market)
    parentCoin, childCoin = market.split('_')
    if getAvailCoin(api, parentCoin) < allowance or allowance < TRADE_MIN:
        return "%s balance or allowance too low!" % parentCoin
    # get 'front'
    price = getFront(api, market, 'buy')
    # amount is in child coins so we need to do the math...
    amount = roundUp(allowance / price)
    # create buy order
    orderNums = [int(
        api.buy(market, price, amount, orderType='postOnly')['orderNumber']
    )]
    while 1:
        for order in api.returnOpenOrders(market):
            if int(order['orderNumber']) != int(orderNums[-1]):
                continue
            logger.debug(order)
            price = getFront(api, market, 'buy')
            if float(order['rate']) < price:
                logger.debug('Moving %s order %s', market, orderNums[-1])
                norder = api.moveOrder(
                    orderNums[-1], price, orderType='postOnly')
                if 'success' in norder and int(norder['success']) == 1:
                    orderNums.append(int(norder['orderNumber']))
                else:
                    logger.error(norder)
                    break
            wait()
            break
        else:
            return orderNums


def checkOrderTrades(api, orderNumber):
    """ Returns False if no trades (or bad order) or returns the trades """
    logger.info('Checking order %s for trades', str(orderNumber))
    try:
        result = api.returnOrderTrades(orderNumber)
        return result
    # no trades yet
    except PoloniexError:
        return False


def getFront(api, market, arg):
    """ Gets 'front' of market and adds/subtracts 1 SATOSHI, if front+SATOSHI
    fills an order, match the front """
    tick = api.returnTicker()[market]
    hbid = float(tick['highestBid'])
    lask = float(tick['lowestAsk'])
    if arg is 'buy':
        if hbid + SATOSHI == lask:
            return hbid
        return hbid + SATOSHI
    if arg is 'sell':
        if lask - SATOSHI == hbid:
            return lask
        return lask - SATOSHI


def getAvailCoin(api, coin):
    """ Returns available <coin> in exchange account """
    bals = api.returnAvailableAccountBalances('exchange')['exchange']
    logger.debug(bals)
    if not coin in bals:
        return 0.0
    return float(bals[coin])


def getLastPoss(api, market, otype, span=5):
    hist = api.returnTradeHistory(market, start=api.DAY * 20)
    rates = []
    for trade in hist:
        if trade['category'] != 'exchange' or trade['type'] != otype:
            continue
        rates.append(float(trade['rate']))
        if len(rates) == span:
            break
    return sum(rates) / len(rates)


class Backtester(object):

    def __init__(self, startAmount=100, parentMin=0.0001, childMin=1.0):
        self.startAmount = float(startAmount)
        self.parentBal = float(startAmount)
        self.childBal = 0.0
        self.parentMin = parentMin
        self.childMin = childMin

    def _backtest(self, row):
        move = float(row['predict']) / 10
        close = float(row['close'])
        # we are buying with movement% of parentBal
        if move > 0:
            if self.parentBal < self.parentMin:
                # not enough bal to make a move
                return self.parentBal + (close * self.childBal)
            # amount to move is the parentBal * move
            prntBamt = self.parentBal * move
            # remove amount from parent bal
            self.parentBal -= prntBamt
            # add amount to child bal
            self.childBal += prntBamt / close

        # we are selling with movement% of childbal
        if move < 0:
            if self.childBal < self.childMin:
                # not enough bal to make a move
                return self.parentBal + (close * self.childBal)
            cldSamt = self.childBal * abs(move)
            self.childBal -= cldSamt
            self.parentBal += close * cldSamt
        return self.parentBal + (close * self.childBal)

    def totals(self):
        return self.parentBal, self.childBal

    def backtest(self, df, **kwargs):
        self.startAmount = kwargs.get('startAmount', self.startAmount)
        self.parentMin = kwargs.get('parentMin', self.parentMin)
        self.childMin = kwargs.get('childMin', self.childMin)
        self.parentBal = self.startAmount
        self.childBal = 0.0
        return df.apply(self._backtest, axis=1)
