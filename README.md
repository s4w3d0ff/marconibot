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
There is an example config located in https://github.com/s4w3d0ff/marconibot/examples. If you run the `bin/marconi` script it will create a data directory in your home folder named '.marconi' and throw an error ``"'MARKET_PAIR.json' files need to be created in..."``. Copy the json file from the examples directory to the created '.marconi' directory and run the bin/marconi script again. It should look similar this:
```
s4w3d0ff@8core~> marconi
Traceback (most recent call last):
  File "/home/s4w3d0ff/.local/bin/marconi", line 4, in <module>
    __import__('pkg_resources').run_script('marconi==0.1.2', 'marconi')
  File "/usr/local/lib/python3.5/dist-packages/pkg_resources/__init__.py", line 748, in run_script
    self.require(requires)[0].run_script(script_name, ns)
  File "/usr/local/lib/python3.5/dist-packages/pkg_resources/__init__.py", line 1517, in run_script
    exec(code, namespace, namespace)
  File "/home/s4w3d0ff/.local/lib/python3.5/site-packages/marconi-0.1.2-py3.5.egg/EGG-INFO/scripts/marconi", line 43, in <module>
    bot = Marconi(datadir)
  File "/home/s4w3d0ff/.local/lib/python3.5/site-packages/marconi-0.1.2-py3.5.egg/marconi/__init__.py", line 156, in __init__
    "'MARKET_PAIR.json' files need to be created in %s" % self.configDir)
RuntimeError: 'MARKET_PAIR.json' files need to be created in /home/s4w3d0ff/.marconi
```
Move json file to .marconi folder, then:
```
s4w3d0ff@8core~> marconi
[20:27:01]marconi.INFO> Building training dataset
[20:27:02]marconi.market.INFO> Getting new BTC_ETH candles from Poloniex...
[20:27:02]marconi.market.INFO> Updating BTC_ETH-chart with 2 new entrys!...
[20:27:02]marconi.market.INFO> Getting BTC_ETH chart data from db
[20:27:02]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:02]marconi.INFO> Adding BTC_ETH labels
[20:27:03]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:03]marconi.INFO> Adding BTC_ETH labels
[20:27:04]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:04]marconi.INFO> Adding BTC_ETH labels
[20:27:04]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:04]marconi.INFO> Adding BTC_ETH labels
[20:27:05]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:05]marconi.INFO> Adding BTC_ETH labels
[20:27:05]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:05]marconi.INFO> Adding BTC_ETH labels
[20:27:06]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:06]marconi.INFO> Adding BTC_ETH labels
[20:27:07]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:07]marconi.INFO> Adding BTC_ETH labels
[20:27:07]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:07]marconi.INFO> Adding BTC_ETH labels
[20:27:08]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:08]marconi.INFO> Adding BTC_ETH labels
[20:27:09]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:09]marconi.INFO> Adding BTC_ETH labels
[20:27:09]marconi.market.INFO> Adding indicators to BTC_ETH dataframe
[20:27:09]marconi.INFO> Adding BTC_ETH labels
[20:27:10]marconi.brain.INFO> Training with 73608 samples
[20:27:12]marconi.market.INFO> BTC_ETH thread started
^C
[20:27:24]marconi.market.INFO> BTC_ETH thread joined
[20:27:24]marconi.INFO> Saving all markets
[20:27:24]marconi.INFO> /home/s4w3d0ff/.marconi/BTC_ETH.json saved
[20:27:24]marconi.brain.INFO> Brain /home/s4w3d0ff/.marconi/BTC_ETH.pickle saved
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
