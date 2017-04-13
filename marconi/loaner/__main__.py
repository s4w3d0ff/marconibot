#!/usr/bin/python

if __name__ == '__main__':
    from . import Loaner, logging, sleep
    from poloniex import Poloniex
    from sys import argv
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    key, secret = argv[1:3]
    loaner = Loaner(Poloniex(key, secret, jsonNums=float))
    loaner.start()
    while loaner._running:
        try:
            sleep(1)
        except:
            loaner.stop()
