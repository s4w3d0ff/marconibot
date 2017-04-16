#!/usr/bin/python

if __name__ == '__main__':
    from tools import Poloniex, logging
    from . import Market
    from pprint import PrettyPrinter

    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    pp = PrettyPrinter(indent=4)

    USDT_BTC = Market("usdt_btc", Poloniex(jsonNums=float))

    pp.pprint(USDT_BTC())
