#!/usr/bin/python

if __name__ == "__main__":
    from . import Lurker, logging, sleep, logger
    from tools import Poloniex
    logging.basicConfig(format='[%(asctime)s]%(message)s',
                        datefmt="%H:%M:%0S", level=logging.INFO)
    troll = Lurker(Poloniex())
    troll.start()
    while 1:
        try:
            sleep(1)
        except:
            troll.stop()
            break
    print(troll())
