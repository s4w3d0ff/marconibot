#!/usr/bin/python

if __name__ == '__main__':
    from . import Loaner, logging
    from time import sleep
    from poloniex import Poloniex
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    key = str(input('key:')).strip()
    secret = str(input('secret:')).strip()
    loaner = Loaner(Poloniex(key, secret, jsonNums=float))
    loaner.start()
    while 1:
        try:
            sleep(1)
        except:
            break
    loaner.stop()
