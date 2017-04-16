from tools import Poloniex, geoProgress, izip
from minion import Minion
from market import Market

from . import logger

if __name__ == '__main__':
    from ticker import Ticker
    ticker.start()
    while True:
        try:
            sleep(4)
        except:
            break
    ticker.stop()
