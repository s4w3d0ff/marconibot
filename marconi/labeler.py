import cherrypy as cp
from bs4 import BeautifulSoup as bs

import pandas as pd
from pymongo import MongoClient
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import NumeralTickFormatter


indexHTML = """
    <!DOCTYPE html><html>
    <head><title>Label Me</title>
    <link href="http://cdn.pydata.org/bokeh/release/bokeh-0.12.6.min.css"
        rel="stylesheet" type="text/css">
    <link href="http://cdn.pydata.org/bokeh/release/bokeh-widgets-0.12.6.min.css"
        rel="stylesheet" type="text/css">
    <script src="http://cdn.pydata.org/bokeh/release/bokeh-0.12.6.min.js"></script>
    <script src="http://cdn.pydata.org/bokeh/release/bokeh-widgets-0.12.6.min.js"></script>
    </head>
    <body>
    <script type="text/javascript">
      function sell() {
          window.location.href = "/sell";
          };
      function buy() {
          window.location.href = "/buy";
          };
      function hold() {
          window.location.href = "/hold";
          };
    </script>
    <button onclick="sell()">sell</button>
    <button onclick="hold()">hold</button>
    <button onclick="buy()">buy</button>
    </body>
    </html>
    """


def plotCandlesticks(p, df, plotwidth=750, upcolor='green', downcolor='red'):
    # set candlewidth based on time gap between candles
    print('Here')
    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
    # Plot candle 'shadows'/wicks
    p.segment(x0=df.date,
              y0=df.high,
              x1=df.date,
              y1=df.low,
              color="black",
              line_width=4)
    # Plot green candles
    inc = df.close > df.open
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.open[inc],
           bottom=df.close[inc],
           fill_color=upcolor,
           line_width=2,
           line_color=upcolor)
    # Plot red candles
    dec = df.open > df.close
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=df.open[dec],
           bottom=df.close[dec],
           fill_color=downcolor,
           line_width=2,
           line_color=downcolor)


class Root(object):

    def __init__(self, market='USDT_BTC', period=60 * 60 * 24):
        self.loc = 0
        self.db = MongoClient()['poloCharts'][market + '-' + str(period)]
        self.df = pd.DataFrame(list(self.db.find()))
        self.df['date'] = pd.to_datetime(self.df["_id"], unit='s')
        print(self.df.tail())

    @cp.expose
    def index(self):
        # find the start and end of frame
        start = self.loc - 7
        if start < 0:
            start = 0
        end = self.loc + 30

        # get current frame of df
        frame = self.df.iloc[start:end]

        # create figure
        p = figure(
            x_axis_type="datetime",
            # y_range=(min(frame['low'].values) - (min(frame['low'].values) * 0.2),
            #         max(frame['high'].values) * 1.2),
            tools="pan,wheel_zoom,reset",
            plot_width=1500,
            toolbar_location="above")
        # format price labels
        p.yaxis[0].formatter = NumeralTickFormatter(format='0.00000000')
        # plot candlesticks
        plotCandlesticks(p, frame)
        # mark current location
        p.circle(x=[self.df.iloc[self.loc]['date']],
                 y=[self.df.iloc[self.loc]['close']],
                 alpha=0.5, size=100)

        # get html and js for chart
        bkscript, bkdiv = components(p)
        # join html
        html = bs(indexHTML, 'html.parser')
        html.body.append(bs(bkscript, 'html.parser'))
        html.body.append(bs(bkdiv, 'html.parser'))
        return html.prettify()

    @cp.expose
    def buy(self):
        self.db.update_one({'_id': self.df.iloc[self.loc]['_id']},
                           {"$set": {'label': 1}},
                           upsert=True)
        self.loc += 1
        raise cp.HTTPRedirect("/")

    @cp.expose
    def sell(self):
        self.db.update_one({'_id': self.df.iloc[self.loc]['_id']},
                           {"$set": {'label': -1}},
                           upsert=True)
        self.loc += 1
        raise cp.HTTPRedirect("/")

    @cp.expose
    def hold(self):
        self.db.update_one({'_id': self.df.iloc[self.loc]['_id']},
                           {"$set": {'label': 0}},
                           upsert=True)
        self.loc += 1
        raise cp.HTTPRedirect("/")

if __name__ == "__main__":
    cp.config.update({'server.socket_port': 8008})
    # run the application
    cp.quickstart(Root(), '/')
