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
# install binarys so we dont have to build from source
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
  | # Built by marconi.poloniex.Ticker ============================
 (( ticker ))------------+{'_id': str(currencyPair),
  |                        'id': float(),
  |                        'last': float(),
  |                        'lowestAsk': float(),
  |                        'highestBid': float(),
  |                        'percentChange': float(),
  |                        'baseVolume': float(),
  |                        'quoteVolume': float(),
  |                        'isFrozen': float(),
  |                        'high24hr': float(),
  |                        'low24hr': float()}+,
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
  |
  |
  | # Built by marconi.trading.Loaner ============================
 (( lendingHistory ))----+{'_id': loan['id'],
  |                         }+,
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
  |
  |
  | # Built by marconi.trading.Bookie ============================
 (( 'market'tradeHistory ))
  |          -----------+{'_id': trade['globalTradeID'],
  |                         }+
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
  |
  |
  | # Built by marconi.market.Market ===================
 (( 'market'chart ))
  |          -----------+{'_id': candle['date'],
  |                         }+
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
  |
  |

```
Drop 'poloniex' Database:
```bash
python3 -c "import pymongo; pymongo.MongoClient().drop_database('poloniex')"
```
