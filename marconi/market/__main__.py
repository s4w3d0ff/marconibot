#!/usr/bin/python

if __name__ == '__main__':
    from tools import Poloniex, logging
    from . import Market
    from sys import argv
    from pprint import PrettyPrinter

    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    key, secret = argv[1:3]

    pp = PrettyPrinter(indent=4)

    USDT_BTC = Market("usdt_btc", Poloniex(key, secret, jsonNums=float))

    pp.pprint(USDT_BTC.db.find_one({'_id': 'USDT_BTC'}))
