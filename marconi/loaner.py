#!/usr/bin/python
# local
from tools import UTCstr2epoch, time, sleep
from tools.trading import autoRenewAll
from . import logger, Minion


class Loaner(Minion):
    """ Loanbot class [API REQUIRES KEY AND SECRET!]"""

    def __init__(self,
                 api,
                 coins={'BTC': 0.01, 'LTC': 0.1, 'ETH': 0.1},
                 maxage=60 * 30,
                 offset=3,
                 delay=60):
        super(Minion, self).__init__()
        self.api = api
        # delay between loops
        self.delay = delay
        # coins to loan out and min amount per coin to create loan
        self.coins = coins
        # maximum age for loan offers before canceled
        self.maxage = maxage
        # number of 'loan-toshis' to offset loan orders from the highest rate
        self.offset = offset

    @property
    def accountBalances(self):
        return self.api.returnAvailableAccountBalances()

    @property
    def activeLoans(self):
        return self.api.returnActiveLoans()

    @property
    def openOffers(self):
        return self.api.returnOpenLoanOffers()

    def getLoanOfferAge(self, order):
        return time() - UTCstr2epoch(order['date'])

    def cancelOldOffers(self):
        offers = self.openOffers
        for coin in self.coins:
            if coin not in offers:
                continue
            for offer in offers[coin]:
                if self.getLoanOfferAge(offer) > self.maxage:
                    self.api.cancelLoanOffer(offer['id'])

    def createLoanOffer(self, coin):
        orders = self.returnLoanOrders(coin)['offers']
        topRate = float(orders['offers'][0]['rate'])
        amount = self.accountBalances['lending'][coin]
        if float(amount) < self.coins[coin]:
            return "%s balance below minimum" % coin
        price = topRate + (self.offset * 0.000001)
        return self.api.createLoanOrder(coin, amount, price, autoRenew=0)

    def run(self):
        """ Main loop, cancels 'stale' loan offers, turns auto-renew off on
        active loans, and creates new loan offers at optimum price """
        while self._running:
            try:
                # Check auto renew is not enabled
                autoRenewAll(self.api, False)
                for coin in self.coins:
                    # Check for old offers
                    self.cancelOldOffers()
                    # Create new offer (if can)
                    self.createLoanOffer(coin)

            except Exception as e:
                logging.exception(e)

            finally:
                # sleep with one eye open...
                for i in range(int(self.delay)):
                    if not self._running:
                        break
                    sleep(1)
