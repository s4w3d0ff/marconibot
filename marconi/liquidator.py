from tools import (
    cancelAllLoanOffers, cancelAllOrders, closeAllMargins, autoRenewAll)
from tools.minion import Minion


class Liquidator(Minion):

    def __init__(self, api, **kwargs):
        self.api = api
        self.coin = kwargs.get('coin', 'BTC')
        self.address = kwargs.get('address', False)

    def run(self, coin, address=False):
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
        # 'dump' all coins at highestBid and buy <coin>
        # withdraw to external <coin> address (if specifiyed)
        return
