
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from . import Marconi
    from sys import argv
    key, secret = argv[1:3]
    marconi = Marconi(key, secret)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)
    marconi.start()
    while True:
        try:
            sleep(4)
        except:
            marconi.stop()
            break
