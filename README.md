[![Build Status](https://travis-ci.org/s4w3d0ff/marconibot.svg?branch=master)](https://travis-ci.org/s4w3d0ff/marconibot)  
![marconi](images/marconi.jpeg)  
Poloniex Trading Bot Toolkit

### Requirements:
__system__:
```
Python 3 (can be installed for Python 2 but parts may not work)
Mongodb (running local)
```
__pip__:
```
scipy
numpy
pandas
scikit-learn
requests
websocket-client
bokeh
pymongo
```

### Quick Linux Install
```bash
# make sure package manager is up to date
pip3 install -U pip wheel setuptools
# install binaries so we dont have to build from source
pip3 install --only-binary=numpy,scipy,pandas,scikit-learn numpy scipy pandas scikit-learn
# install this repo
pip3 install git+https://github.com/s4w3d0ff/marconibot.git
```

### Mongo Tree:
```
 ( )  = database
(( )) = collection/table
+{ }+ = document

( poloniex )
  |
  |
  | # Built by marconi.market.Market ===================
 (( 'market'-chart ))
  |          -----------+{'_id': candle['date'],
  |                         }+
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
 (( 'market'-tradeHistory ))
  |          -----------+{'_id': trade['globalTradeID'],
  |                         }+
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
 (( lendingHistory ))----+{'_id': loan['id'],
  |                         }+,
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
```
Drop 'poloniex' Database:
```bash
python3 -c "import pymongo; pymongo.MongoClient().drop_database('poloniex')"
```
### Running the example bot:
There is an example config located in [marconibot/examples](https://github.com/s4w3d0ff/marconibot/tree/master/examples). If you run the `bin/marconi` script it will create a data directory in your home folder named '.marconi' and throw an error ``"A 'marconi.json' file needs to be created in..."``. Copy the json file in the examples directory to the created '.marconi' directory
and run the bin/marconi script again. It should look similar this:
```
s4w3d0ff@8core~> marconi
Traceback (most recent call last):
  File "/home/s4w3d0ff/.local/bin/marconi", line 4, in <module>
    __import__('pkg_resources').run_script('marconi==0.1.2', 'marconi')
  File "/usr/local/lib/python3.5/dist-packages/pkg_resources/__init__.py", line 742, in run_script
    self.require(requires)[0].run_script(script_name, ns)
  File "/usr/local/lib/python3.5/dist-packages/pkg_resources/__init__.py", line 1503, in run_script
    exec(code, namespace, namespace)
  File "/home/s4w3d0ff/.local/lib/python3.5/site-packages/marconi-0.1.2-py3.5.egg/EGG-INFO/scripts/marconi", line 97, in <module>
    "A 'marconi.json' file needs to be created in %s", dataDir)
RuntimeError: ("A 'marconi.json' file needs to be created in %s", '/home/s4w3d0ff/.marconi')
```
Move json file to .marconi folder, then:
```
s4w3d0ff@8core~> marconi
[12:43:00]marconi.INFO> Training Brain
[12:43:00]marconi.brain.INFO> Building training dataset
[12:43:00]marconi.market.INFO> Getting new BTC_ETH candles from Poloniex...
[12:43:00]urllib3.connectionpool.DEBUG> Starting new HTTPS connection (1): poloniex.com
[12:43:01]urllib3.connectionpool.DEBUG> https://poloniex.com:443 "GET /public?command=returnChartData&start=1504121400&currencyPair=BTC_ETH&end=1504122180.4097323&period=300 HTTP/1.1" 200 None
[12:43:01]marconi.market.INFO> Updating BTC_ETH-chart with 3 new entrys!...
[12:43:01]marconi.market.INFO> Getting BTC_ETH chart data from db
[12:43:02]marconi.market.DEBUG> Zooming BTC_ETH dataframe...
[12:43:02]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[12:43:02]marconi.brain.DEBUG> Adding labels
[12:43:09]marconi.market.INFO> Getting new BTC_XMR candles from Poloniex...
[12:43:09]urllib3.connectionpool.DEBUG> Starting new HTTPS connection (1): poloniex.com
[12:43:09]urllib3.connectionpool.DEBUG> https://poloniex.com:443 "GET /public?command=returnChartData&start=1504121400&currencyPair=BTC_XMR&end=1504122189.2205427&period=300 HTTP/1.1" 200 None
[12:43:09]marconi.market.INFO> Updating BTC_XMR-chart with 3 new entrys!...
[12:43:09]marconi.market.INFO> Getting BTC_XMR chart data from db
[12:43:11]marconi.market.DEBUG> Zooming BTC_XMR dataframe...
[12:43:11]marconi.market.INFO> Adding indicators to BTC_XMR dataframe
[12:43:11]marconi.brain.DEBUG> Adding labels
[12:43:15]marconi.brain.INFO> Training with 82128 samples
[12:43:17]marconi.INFO> /home/s4w3d0ff/.marconi/marconi.json saved
[12:43:17]marconi.brain.INFO> Brain /home/s4w3d0ff/.marconi/marconi.pickle saved
[12:43:17]marconi.market.INFO> BTC_ETH thread started
[12:43:17]marconi.market.INFO> Getting new BTC_ETH candles from Poloniex...
[12:43:17]urllib3.connectionpool.DEBUG> Starting new HTTPS connection (1): poloniex.com
[12:43:17]urllib3.connectionpool.DEBUG> https://poloniex.com:443 "GET /public?command=returnChartData&start=1504122000&currencyPair=BTC_ETH&end=1504122197.3275995&period=300 HTTP/1.1" 200 None
[12:43:17]marconi.market.INFO> Updating BTC_ETH-chart with 1 new entrys!...
[12:43:17]marconi.market.INFO> Getting BTC_ETH chart data from db
[12:43:17]marconi.market.DEBUG> Zooming BTC_ETH dataframe...
[12:43:17]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[12:43:17]marconi.brain.DEBUG> Adding labels
[12:43:17]__main__.INFO> BTC_ETH brain score: 0.999305072967
[12:43:17]marconi.trading.INFO> Backtesting...
[12:43:18]__main__.INFO> BTC_ETH
                        close  predict   btStart   btTotal  btProfit
date                                                                
2017-08-23 19:50:00  0.077090        0  8.312700  8.312700       0.0
2017-08-23 19:57:00  0.077611        0  8.328332  8.328332       0.0
2017-08-23 20:04:00  0.077475        0  8.324241  8.324241       0.0
2017-08-23 20:11:00  0.077300        0  8.319000  8.319000       0.0
2017-08-23 20:18:00  0.077127        0  8.313800  8.313800       0.0
                        close  predict   btStart   btTotal  btProfit
date                                                                
2017-08-30 19:08:00  0.084280        0  8.528389  8.528110 -0.000279
2017-08-30 19:15:00  0.084495        0  8.534853  8.534553 -0.000300
2017-08-30 19:22:00  0.084500        0  8.535000  8.534700 -0.000300
2017-08-30 19:29:00  0.084600        0  8.538000  8.537690 -0.000310
2017-08-30 19:36:00  0.084454        0  8.533630  8.533334 -0.000296
^C
[12:43:25]marconi.INFO> Stopping all markets
[12:43:26]marconi.market.INFO> BTC_ETH thread joined
[12:43:26]marconi.INFO> Markets stopped
```
You should now have a .pickle file in the same directory as your json file. The .json file has also been updated with the location of the newly saved .pickle file. The .pickle file is the saved `marconi.brain.Brain.lobe` which can be loaded into a fresh brain using: `marconi.brain.Brain.load()`


## Exmple library use:

### The `marconi.market.Market` class:
```
Python 3.5.2 (default, Nov 17 2016, 17:05:23)
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import marconi
>>> market = marconi.Market(api=marconi.Poloniex(), pair='BTC_ETH')
>>> dir(market)
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'addStopOrder', 'api', 'availBalances', 'cancelOrders', 'cancelStopOrder', 'chart', 'child', 'dump', 'getOrder', 'moveToFront', 'myLendingHistory', 'myTradeHistory', 'openOrders', 'pair', 'parent', 'pump', 'stops', 'tick']
>>> market.tick
Ticker is not running!
{'last': '0.08422377', 'highestBid': '0.08414157', 'isFrozen': '0', 'high24hr': '0.08480000', 'lowestAsk': '0.08420000', 'id': 148.0, 'low24hr': '0.08000501', 'baseVolume': '13825.18116127', 'percentChange': '0.04214239', 'quoteVolume': '167371.25792035'}
>>> market.tick
Ticker is not running!
{'last': '0.08414200', 'highestBid': '0.08414771', 'isFrozen': '0', 'high24hr': '0.08480000', 'lowestAsk': '0.08420000', 'id': 148.0, 'low24hr': '0.08000501', 'baseVolume': '13825.18116127', 'percentChange': '0.04113061', 'quoteVolume': '167371.25792035'}
>>> market.api.startWebsocket()
>>> market.tick
{'last': 0.08415001, 'highestBid': 0.08415001, 'isFrozen': 0.0, 'high24hr': 0.0848, 'lowestAsk': 0.0842, 'id': 148.0, 'low24hr': 0.08000501, 'baseVolume': 13835.01093174, 'percentChange': 0.04122959, 'quoteVolume': 167487.02060288}
>>>
```
