#!/usr/bin/python

if __name__ == '__main__':
    from . import Loaner, logging
    logging.basicConfig(level=logging.DEBUG)

    loaner = Loaner(Poloniex(key, secret, jsonNums=float))
    loaner.start()
