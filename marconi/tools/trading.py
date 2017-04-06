from . import logger, PHI


def trend(seq):
    """
    Basic trend calculation by splitting the <seq> data in half, find the
    mean of each half, then subtract the old half from the new half. A
    negitive number represents a down trend, positive number is an up trend.
    >>> trend([1.563, 2.129, 3.213, 4.3425, 5.1986, 5.875644])
    2.866122
    """
    half = len(seq) // 2
    return average(seq[half:]) - average(seq[:-half])


def average(seq):
    """
    Finds the average of <seq>
    >>> average(['3', 9.4, '0.8888', 5, 1.344444, '3', '5', 6, '7'])
    4.033320571428571
    """
    return sum(seq) / len(seq)


def geoProgress(n, r=PHI, size=5):
    """ Creates a Geometric Progression with the Geometric sum of <n> """
    return [(n * (1 - r) / (1 - r ** size)) * r ** i for i in range(size)]


def cancelAllOrders(api, market, arg=False):
    """ Cancels all orders for a market. Can be limited to just buy or sell
        orders using the 'arg' param """
    orders = api.returnOpenOrders(market)
    if market == 'all':
        nOrders = []
        for market in orders:
            for order in orders[market]:
                nOrders.append(order)
        orders = nOrders

    # cancel just buy or sell
    if arg in ('sell', 'buy')
        for o in orders:
            if o['type'] == arg:
                logger.info(api.cancelOrder(o["orderNumber"]))
    # cancel all
    else:
        for o in orders:
            logger.info(api.cancelOrder(o["orderNumber"]))


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
            api.toggleAutoRenew(loan['id'])
