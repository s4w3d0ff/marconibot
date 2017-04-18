from tools import Poloniex, sleep, satoshi, tradeMin, logging, Process
from tools.chart import Chart
from ticker import Ticker
from loaner import Loaner
from lurker import Lurker

logger = logging.getLogger(__name__)


class Marconi(object):

    def __init__(self, key, secret):
        self.api = Poloniex(key, secret, jsonNums=float)
        self._running, self._process = False, None
        self.bots = {
            'loaner': Loaner(self.api),
            'ticker': Ticker(self.api),
            'lurker': Lurker(self.api)
        }
        self.coins = {}

    def start(self):
        """ Start all loaded bots/minions and start 'run' process"""
        for bot in self.bots:
            logger.info('Starting %s', bot)
            self.bots[bot].start()
        self._running = True
        self._process = Process(target=self.run)
        self._process.daemon = True
        self._process.start()

    def stop(self):
        """ Stop all running bots/minions and stop main process"""
        for bot in self.bots:
            logger.info('Stopping %s', bot)
            self.bots[bot].start()
        self._running = False
        try:
            self._process.terminate()
        except:
            pass
        try:
            self._process.join()
        except:
            pass

    def run(self):
        while self._running:
            sleep(2)
            """
            # get available bals
            bals = self.api.returnAvailableAccountBalances()
            # if we have btc in exchange account
            if 'exchange' in bals and 'BTC' in bals['exchange']:
                # buy loanable coin(s) at dip (using bbands for optimum price)

                #   see if we made any fees from matured loans
                #   if we made enough fees to make a trade and price is above profitMin:
                #       move fees to exchange account
                #       sell fees for btc
            """
