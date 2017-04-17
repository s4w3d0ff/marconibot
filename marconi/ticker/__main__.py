#!/usr/bin/python

if __name__ == '__main__':
    from tools import sleep, logging, Poloniex
    from . import Ticker
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    ticker = Ticker(Poloniex(jsonNums=float))
    ticker.start()
    while ticker._running:
        try:
            logging.info('USDT_BTC last: %s' % ticker('USDT_BTC')['last'])
            sleep(10)
        except Exception as e:
            logging.exception(e)
            ticker.stop()
