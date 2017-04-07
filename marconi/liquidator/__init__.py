from tools import (
    cancelAllLoanOffers, cancelAllOrders, closeAllMargins, autoRenewAll)
from minion import Minion


class Liquidator(Minion):

    def __init__(self, api, **kwargs):
        super(Minion, self).__init__()
        self.api = api
        self.coin = kwargs.get('coin', 'BTC')
        self.address = kwargs.get('address', False)

    def run(self):
        """ Main loop """
        pass

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
