#!/usr/bin/python
from tools import UTCstr2epoch, time, sleep, autoRenewAll, logging
from tools import BL, OR, RD, GY, GR
from tools.minion import Minion


logger = logging.getLogger(__name__)


class Loaner(Minion):
    """ Loanbot class [API REQUIRES KEY AND SECRET!]"""

    def __init__(self,
                 api,
                 coins={'BTC': 0.01},
                 maxage=60 * 5,
                 delay=60 * 3):
        self.api, self.delay = api, delay
        self.coins, self.maxage = coins, maxage

    def getLoanOfferAge(self, order):
        return time() - UTCstr2epoch(order['date'])

    def cancelOldOffers(self):
        logger.info(GR("Checking Open Loan Offers:----------------"))
        offers = self.api.returnOpenLoanOffers()
        for coin in self.coins:
            if coin not in offers:
                continue
            for offer in offers[coin]:
                logger.info("%s|%s:%s-[rate:%s]",
                            BL(offer['date']),
                            OR(coin),
                            RD(offer['amount']),
                            GY(str(float(offer['rate']) * 100) + '%')
                            )
                if self.getLoanOfferAge(offer) > self.maxage:
                    logger.info("Canceling %s offer %s",
                                OR(coin), GY(str(offer['id'])))
                    r = self.api.cancelLoanOffer(offer['id'])
                    logger.info(r['message'])

    def createLoanOffers(self):
        logger.info(GR("Checking for coins to lend:---------------"))
        bals = self.api.returnAvailableAccountBalances()
        if not 'lending' in bals:
            return logger.info(RD("No coins found in lending account"))
        for coin in self.coins:
            if coin not in bals['lending']:
                continue
            amount = bals['lending'][coin]
            if float(amount) < self.coins[coin]:
                logger.info("Not enough %s:%s, below set minimum: %s",
                            OR(coin),
                            RD(str(amount)),
                            BL(str(self.coins[coin])))
                continue
            else:
                logging.info("%s:%s", OR(coin), GR(str(amount)))
            orders = self.api.returnLoanOrders(coin)['offers']
            price = sum([float(o['rate']) for o in orders]) / len(orders)
            logger.info('Creating %s %s loan offer at %s',
                        RD(str(amount)), OR(coin), GR(str(price * 100) + '%'))
            r = self.api.createLoanOffer(coin, amount, price, autoRenew=0)
            logger.info('%s', GR(r["message"]))

    def run(self):
        """ Main loop, cancels 'stale' loan offers, turns auto-renew off on
        active loans, and creates new loan offers at optimum price """
        # Check auto renew is not enabled for current loans
        autoRenewAll(self.api, toggle=False)
        while self._running:
            try:
                # Check for old offers
                self.cancelOldOffers()
                # Create new offer (if can)
                self.createLoanOffers()
                # show active
                active = self.api.returnActiveLoans()['provided']
                logger.info(GR('Active Loans:-----------------------------'))
                for i in active:
                    logger.info('%s|%s:%s-[rate:%s]-[fees:%s]',
                                BL(i['date']),
                                OR(i['currency']),
                                RD(i['amount']),
                                GY(str(float(i['rate']) * 100) + '%'),
                                GR(i['fees'])
                                )

            except Exception as e:
                logger.exception(e)

            finally:
                # sleep with one eye open...
                for i in range(int(self.delay)):
                    if not self._running:
                        break
                    sleep(1)

if __name__ == '__main__':
    from sys import argv
    from tools import Poloniex
    logging.basicConfig(
        format='[%(asctime)s]%(message)s',
        datefmt=GR("%H:%M:%S"),
        level=logging.INFO
    )
    logging.getLogger('requests').setLevel(logging.ERROR)
    key, secret = argv[1:3]
    polo = Poloniex(key, secret, timeout=80, jsonNums=float)
    #################-Configure Below-##################################
    ########################
    loaner = Loaner(polo,
                    # This dict defines what coins the bot should worry about
                    # The dict 'key' is the coin to lend, 'value' is the
                    # minimum amount to lend
                    coins={
                        'DASH': 1,
                        'BTC': 0.01,
                        'LTC': 1
                    },
                    # Maximum age (in secs) to let an open offer sit
                    maxage=60 * 15,  # 5 min
                    # number of seconds between loops
                    delay=60 * 5)  # 3 min
    ########################
    #################-Stop Configuring-#################################

    loaner.start()
    while loaner._running:
        try:
            sleep(1)
        except:
            loaner.stop()
            break
