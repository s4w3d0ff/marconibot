#!/usr/bin/python

if __name__ == '__main__':
    from tools import sleep, logging, Poloniex
    from . import Ticker
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=4)
    logging.basicConfig(level=logging.DEBUG)
    ticker = Ticker(Poloniex(jsonNums=float))
    ticker.start()
    sleep(5)
    while ticker._running:
        try:
            pp.pprint(ticker('USDT_BTC'))
            pp.pprint(ticker('USDT_LTC'))
            pp.pprint(ticker('BTC_DOGE'))
            sleep(10)
        except Exception as e:
            print(e)
            ticker.stop()
