from tools.trading import (
    cancelAllLoanOffers, cancelAllOrders, closeAllMargins, autoRenewAll
)
from . import logger, Thread


class Liquidator(object):

    def __init__(self, api, **kwargs):
        self.api = api
        self.coin = kwargs.get('coin', 'BTC')
        self.address = kwargs.get('address', False)
        self._running = False

    def start(self):
        self._thread = Thread(target=self.run)
        self._thread.setDaemon(True)
        self._running = True
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()

    def liquidate(self, coin, address=False):
        """
        Move all assets into <coin> and withdraw to external coin
        address (api withdrawing needs to be enabled on poloniex in order to
        withdraw)
        """
        # turn off auto-renew on active loans
        autoRenewAll(self.api, False)
        # cancel loan offers
        cancelAllLoanOffers(self.api)
        # cancel all open orders
        cancelAllOrders(self.api, market='all')
        # close margins
        closeAllMargins(self.api)
        # transfer all funds to 'exchange' account
        accounts = self.api.returnAvailableAccountBalances()
        for c in accounts['lending']:
            self.api.transferBalance(c,
                                     accounts['lending'][c],
                                     'lending',
                                     'exchange')
        for c in accounts['margin']:
            self.api.transferBalance(c,
                                     accounts['margin'][c],
                                     'margin',
                                     'exchange')
        # 'dump' all coins at highestBid and buy <coin>
        # withdraw to external <coin> address (if specifiyed)
        return
