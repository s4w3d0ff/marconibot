#!/usr/bin/python

if __name__ == "__main__":
    from . import Lurker, logging, sleep
    logging.basicConfig(format='[%(asctime)s]%(message)s',
                        datefmt="%H:%M:%0S", level=logging.INFO)
    troll = Lurker()
    troll.start()
    sleep(60 * 3)  # runs for 3 mins then prints scores for coins
    troll.stop()
    print(troll())
