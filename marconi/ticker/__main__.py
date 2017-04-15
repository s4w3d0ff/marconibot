#!/usr/bin/python

if __name__ == '__main__':
    from tools import sleep, logging, Poloniex
    from . import Ticker
    logging.basicConfig(level=logging.DEBIG)
    ticker = Ticker(Poloniex())
    ticker.start()
    while ticker._running:
        try:
            sleep(1)
        except:
            ticker.stop()
