from tools import Poloniex, sleep
from . import logger
from ticker import Ticker

if __name__ == '__main__':
    ticker.start()
    while True:
        try:
            sleep(4)
        except:
            break
    ticker.stop()
