from . import time, getMongoDb, indica, logging, izip, addDoji, pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')

logger = logging.getLogger(__name__)


class Chart(object):
    """ Saves and retrieves chart data for a market """

    def __init__(self, api, pair, **kwargs):
        """
        pair = market pair
        api = poloniex api object
        frame = time frame of chart (default: 1 Day)
        period = time period of candles (default: 5 Min)
        window = number of candles to use for roc, rsi, wma (default: 60)
        """
        self.db = getMongoDb('markets')
        self.pair = pair
        self.api = api
        self.frame = kwargs.get('frame', self.api.DAY * 7)
        self.period = kwargs.get('period', self.api.MINUTE * 5)
        self.window = kwargs.get('window', 120)

    def __call__(self):
        try:  # look for old timestamp
            timestamp = self.db.find_one({
                '_id': self.pair})['chart']['timestamp']
        except:  # not found
            timestamp = 0
        if time() - timestamp > 60:
            logger.info('%s chart db updating...', self.pair)
            raw = self.api.returnChartData(
                self.pair, self.period, time() - self.frame)
            aves = [i['weightedAverage'] for i in raw]
            # bbands is the shortest list
            # so slice the base data by bbands size (from rear)
            bbands = indica.bb(aves, self.window * 2).tolist()
            raw = raw[-len(bbands):]
            for i, data in izip(range(len(raw)), bbands):
                # upper, middle, lower bands, bandwidth, range and %B
                raw[i]['bb_high'], raw[i]['sma'], raw[i]['bb_low'], raw[i][
                    'bb_width'], raw[i]['bb_range'], raw[i]['bb_percent'] = data
            for i, data in izip(
                    range(len(raw)), indica.roc(aves, self.window).tolist()):
                raw[i]['roc'] = data
            for i, data in izip(
                    range(len(raw)), indica.rsi(aves, self.window).tolist()):
                raw[i]['rsi'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, self.window, 0.1, 3).tolist()):
                raw[i]['wma_high'], raw[i]['wma'], raw[i]['wma_low'], raw[
                    i]['wma_range'], raw[i]['wma_percent'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, self.window // 2, 0.1, 0).tolist()):
                raw[i]['ema_high'], raw[i]['ema'], raw[i]['ema_low'], raw[
                    i]['ema_range'], raw[i]['ema_percent'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, (self.window // 2) + 10, 0.1, 1).tolist()):
                raw[i]['slow_ema_high'], raw[i]['slow_ema'], raw[i]['slow_ema_low'], raw[
                    i]['slow_ema_range'], raw[i]['slow_ema_percent'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, (self.window // 2) - 10, 0.1, 2).tolist()):
                raw[i]['fast_ema_high'], raw[i]['fast_ema'], raw[i]['fast_ema_low'], raw[
                    i]['fast_ema_range'], raw[i]['fast_ema_percent'] = data
            for i in range(len(raw)):
                raw[i]['label'] = addDoji(raw[i])

            self.db.update_one(
                {'_id': self.pair},
                {'$set': {
                    "chart": {
                        "frame": self.frame,
                        "period": self.period,
                        "window": self.window,
                        "candles": raw,
                        "timestamp": time()}}
                 },
                upsert=True)
            logger.info('%s chart db updated!', self.pair)
        return self.db.find_one({'_id': self.pair})['chart']

    def getDataFrame(self):
        data = self.__call__()['candles']
        df = pd.DataFrame(data, index=[pd.to_datetime(
            c['date'], unit='s') for c in data])
        del df['date']
        return df

    def show(self):
        df = self.getDataFrame()
        fig, axes = plt.subplots(nrows=2, ncols=1)
        df[['sma', 'bb_high', 'bb_low']].plot(ax=axes[0], colormap='Blues')
        axes[0].set_title(self.pair)
        df[['roc', 'rsi']].plot(subplots=True, ax=axes[1])
        plt.show()

if __name__ == '__main__':
    from poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    api = Poloniex(jsonNums=float)
    chart = Chart(api, 'BTC_LTC')
    print(chart.show())
