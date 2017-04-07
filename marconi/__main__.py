#!/usr/bin/python
from tools import Daemon, Poloniex  # , Coach

PIDPATH = '~/.marconid.pid'

COMMANDS = ('start', 'stop', 'restart')


class Marconid(Daemon):

    def __init__(self, *args, **kwargs):
        super(Daemon, self).__init__(*args, **kwargs)
        self.api = Poloniex(coach=True, jsonNums=float)
        self.bots = {}

    def run(self):
        while True:
            for bot in bots:
                logging.info("%s Running: %s", bot, str(bots[bot]._running))

    def watch(self, market):


if __name__ == '__main__':
    import sys
    d = Watcher(PIDPATH)
    command = str(sys.argv[1]).lower()
    if command not in COMMANDS:
        raise Exception('Invalid command: %s' % command)
    getattr(d, command)(sys.argv[2:])
