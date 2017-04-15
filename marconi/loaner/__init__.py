# local
from tools import UTCstr2epoch, time, sleep, autoRenewAll, logging
from minion import Minion


logger = logging.getLogger(__name__)


class Loaner(Minion):
    """ Loanbot class [API REQUIRES KEY AND SECRET!]"""

    def __init__(self,
                 api,
                 coins={'DASH': 0.1, 'DOGE': 100.0, 'BTC': 0.01, 'LTC': 1},
                 maxage=60 * 30,
                 offset=3,
                 delay=60):
        self.api, self.delay, self.coins, self.maxage, self.offset =\
            api, delay, coins, maxage, offset
        # Check auto renew is not enabled for current loans
        autoRenewAll(self.api, toggle=False)

    def getLoanOfferAge(self, order):
        return time() - UTCstr2epoch(order['date'])

    @property
    def cancelOldOffers(self):
        logger.info('Getting open loan offers')
        offers = self.api.returnOpenLoanOffers()
        for coin in self.coins:
            logger.info('Checking for "stale" %s loans...', coin)
            if coin not in offers:
                logger.info('No open offers found.')
                continue
            for offer in offers[coin]:
                if self.getLoanOfferAge(offer) > self.maxage:
                    logger.info('Canceling offer %s', offer['id'])
                    logger.info(self.api.cancelLoanOffer(offer['id']))

    @property
    def createLoanOffers(self):
        logger.info('Getting account balances')
        bals = self.api.returnAvailableAccountBalances()
        if not 'lending' in bals:
            return logger.info('No coins found in lending account')
        for coin in self.coins:
            if coin not in bals['lending']:
                logger.info("No available %s in lending", coin)
                continue
            amount = bals['lending'][coin]
            if float(amount) < self.coins[coin]:
                logger.info("Not enough %s:%s, below set minimum: %s",
                            coin, str(amount), str(self.coins[coin]))
                continue
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
                # Check for old offers
                self.cancelOldOffers
                # Create new offer (if can)
                self.createLoanOffers
                # show active
                active = self.api.returnActiveLoans()['provided']
                logger.info('Active Loans:----------------')
                for i in active:
                    logger.info('%s[rate:%s] %s:%s [fees:%s]',
                                i['date'],
                                str(float(i['rate']) * 100),
                                i['currency'],
                                i['amount'],
                                i['fees']
                                )

            except Exception as e:
                logger.exception(e)

            finally:
                # sleep with one eye open...
                for i in range(int(self.delay)):
                    if not self._running:
                        break
                    sleep(1)
