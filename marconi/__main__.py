# pip install daemon
from daemon import Daemon
# https://github.com/s4w3d0ff/python-poloniex
from poloniex import Poloniex, Coach
# local
from bots import loaner, liquidator, lurker, ticker

PIDPATH = '~/.marconid.pid'

COMMANDS = ('start', 'stop', 'restart')


class Marconid(Daemon):

    def __init__(self, *args, **kwargs):
        super(Daemon, self).__init__(*args, **kwargs)
        self.api = Poloniex(coach=True, jsonNums=float)
        self.bots = {}
        self.bots['loaner'] = loaner.Loaner(self.api)
        self.bots['lurker'] = lurker.Lurker(self.api)
        self.bots['ticker'] = ticker.Ticker(self.api)
        self.bots['911'] = liquidator.Liquidator(self.api)

    def run(self):
        while True:
            for bot in bots:
                if not bots[bot]._running:
                    bots[bot].start()

if __name__ == '__main__':
    d = Watcher(PIDPATH)
    command = str(sys.argv[1]).lower()
    if command not in COMMANDS:
        raise Exception('Invalid command: %s' % arg)
    getattr(spawn, command)(*argv[2:])
