from tools import copy, itemgetter, figure, pd, cp, MongoClient
from bokeh.embed import components

HTML = BS("""
        <!DOCTYPE html><html>
        <head><title></title>
        <link
        href="http://cdn.pydata.org/bokeh/release/bokeh-0.12.6.min.css"
        rel="stylesheet" type="text/css">
        <link
        href="http://cdn.pydata.org/bokeh/release/bokeh-widgets-0.12.6.min.css"
        rel="stylesheet" type="text/css">

        <script src="http://cdn.pydata.org/bokeh/release/bokeh-0.12.6.min.js"></script>
        <script src="http://cdn.pydata.org/bokeh/release/bokeh-widgets-0.12.6.min.js"></script>
        </head>
        <body><center><center></body>
        </html>""", 'html.parser')

buttons = BS("""
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
        <button onclick="sell()">sell</button><button onclick="hold()">hold</button><button onclick="buy()">buy</button>
        """, 'html.parser')


def plotCandlesticks(p, df, period, upcolor='green', downcolor='red'):
    candleWidth = (period * 900)
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
           line_color="black")
    # Plot red candles
    dec = df.open > df.close
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=df.open[dec],
           bottom=df.close[dec],
           fill_color=downcolor,
           line_color="black")


class Root(object):

    def __init__(self, market, period):
        self.loc = 0
        self.period = period
        self.db = MongoClient()['poloCharts'][market + '-' + str(period)]
        self.df = pd.DataFrame(list(self.db.find())).tail(150)
        if 'label' in self.df:
            self.df['label'].fillna('hold', inplace=True)
        self.df['date'] = pd.to_datetime(self.df["_id"], unit='s')

        print(self.df)

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
        p = figure(x_axis_type="datetime",
                   x_minor_ticks=1000,
                   tools="pan,wheel_zoom,reset",
                   plot_width=1500,
                   toolbar_location="above")
        # plot candlesticks
        plotCandlesticks(p, frame, self.period)
        # mark current location
        p.circle(x=[self.df.iloc[self.loc]['date']], y=[
                 self.df.iloc[self.loc]['close']], alpha=0.5, size=100)
        # get html and js for chart
        script, div = components(p)
        # create html
        html = copy(HTML)
        html.title.string = 'Label Me'
        html.body.append(BS(script, 'html.parser'))
        html.body.append(BS(div, 'html.parser'))
        html.body.append(buttons)
        # return html
        return html.prettify()

    @cp.expose
    def buy(self):
        self.db.update_one({'_id': self.df.iloc[self.loc]['_id']},
                           {"$set": {'label': 'buy'}},
                           upsert=True)
        self.loc += 1
        raise cp.HTTPRedirect("/")

    @cp.expose
    def sell(self):
        self.db.update_one({'_id': self.df.iloc[self.loc]['_id']},
                           {"$set": {'label': 'sell'}},
                           upsert=True)
        self.loc += 1
        raise cp.HTTPRedirect("/")

    @cp.expose
    def hold(self):
        self.db.update_one({'_id': self.df.iloc[self.loc]['_id']},
                           {"$set": {'label': 'hold'}},
                           upsert=True)
        self.loc += 1
        raise cp.HTTPRedirect("/")

if __name__ == "__main__":
    # set the cherrypy server port
    cp.config.update({'server.socket_port': 8008})
    # run the application
    cp.quickstart(Root('USDT_BTC', period=60 * 60 * 24), '/')
