from tools.minion import Minion
from tools import frontBuy, frontSell, wait, logging, checkOrderTrades

logger = logging.getLogger(__name__)


class FrontRunner(Minion):

    def __init__(self, api, market, allowance=0.01):
        self.api, self.market = api, market
        self.allowance = allowance

    def run(self):
        while self._running:
            pass

if __name__ == '__main__':
    from tools import Poloniex
    from sys import argv
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    frontBuy(api, market='BTC_ETH')
