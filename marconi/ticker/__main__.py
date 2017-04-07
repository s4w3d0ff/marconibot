#!/usr/bin/python

if __name__ == '__main__':
    from tools import sleep, logging, Poloniex
    from . import Ticker
    logging.basicConfig(level=logging.DEBIG)
    ticker = Ticker(Poloniex())
    ticker.start()
    for i in range(5):
        sleep(10)
        print("USDT_BTC: lowestAsk= %s" % ticker()['lowestAsk'])
    ticker.stop()
    print("Done")
