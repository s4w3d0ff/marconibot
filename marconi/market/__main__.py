#!/usr/bin/python

if __name__ == '__main__':
    from tools import Poloniex
    from . import Market
    market = Market(pair="usdt_btc", api=Poloniex(jsonNums=float))
    print(market.chart())
