from . import Process, logger


class Minion(object):
    """ Minions control child processes that do the Daemon's bidding. """

    def __init__(self):
        self._running = False
        self._process = None

    def start(self):
        """ Start Minion.run Process """
        self._process = Process(target=self.run)
        self._process.daemon = True
        self._running = True
        self._process.start()

    def stop(self):
        """ Force the Minion to stop """
        self._running = False
        try:
            self._process.terminate()
        except Exception as e:
            logger.exception(e)
        try:
            self._process.join()
        except Exception as e:
            logger.exception(e)

    def run(self):
        """ Method ran in a child process. It should be over written when
        subclassed """
        pass
