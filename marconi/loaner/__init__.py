# local
from tools import UTCstr2epoch, time, sleep, autoRenewAll, logging
from minion import Minion


logger = logging.getLogger(__name__)


class Loaner(Minion):
    """ Loanbot class [API REQUIRES KEY AND SECRET!]"""

    def __init__(self,
                 api,
                 coins={'DASH': 0.1, 'DOGE': 100.0},
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
        logger.info('Getting account balances')
        return self.api.returnAvailableAccountBalances()

    @property
    def activeLoans(self):
        logger.info('Getting active loans')
        return self.api.returnActiveLoans()

    @property
    def openOffers(self):
        logger.info('Getting open loan offers')
        return self.api.returnOpenLoanOffers()

    def getLoanOfferAge(self, order):
        return time() - UTCstr2epoch(order['date'])

    def cancelOldOffers(self):
        offers = self.openOffers
        for coin in self.coins:
            logger.info('Checking for "stale" %s loans...', coin)
            if coin not in offers:
                logger.info('No open offers found.')
                continue
            for offer in offers[coin]:
                if self.getLoanOfferAge(offer) > self.maxage:
                    logger.info('Canceling offer %s', offer['id'])
                    logger.info(self.api.cancelLoanOffer(offer['id']))

    def createLoanOffers(self):
        bals = self.accountBalances['lending']
        for coin in bals:
            amount = bals[coin]
            if float(amount) > self.coins[coin]:
                orders = self.api.returnLoanOrders(coin)['offers']
                topRate = float(orders[0]['rate'])
                price = topRate + (self.offset * 0.000001)
                logger.info('Creating %s %s loan offer at %s',
                            str(amount), coin, str(price))
                logger.info(self.api.createLoanOffer(
                    coin, amount, price, autoRenew=0))

    def run(self):
        """ Main loop, cancels 'stale' loan offers, turns auto-renew off on
        active loans, and creates new loan offers at optimum price """
        while self._running:
            try:
                # Check auto renew is not enabled
                #autoRenewAll(self.api, False)
                # Check for old offers
                self.cancelOldOffers()
                # Create new offer (if can)
                self.createLoanOffers()

            except Exception as e:
                logger.exception(e)

            finally:
                # sleep with one eye open...
                for i in range(int(self.delay)):
                    if not self._running:
                        break
                    sleep(1)
