[![Build Status](https://travis-ci.org/s4w3d0ff/marconibot.svg?branch=master)](https://travis-ci.org/s4w3d0ff/marconibot)  
![marconi](images/marconi.jpeg)  
Poloniex Trading Bot Toolkit

### Requirements:
__system__:
```
Python 3
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

### Mongo Tree:
```
 ( )  = database
(( )) = collection/table
+{ }+ = document

( poloniex )
  |
  | # Built by ticker.py ============================
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
  | # Built by loaner.py ============================
 (( lendingHistory ))----+{'_id': loan['id'],
  |                         }+,
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
  |
  |
  | # Built by bookie.py ============================
 (( 'market'tradeHistory ))
  |          -----------+{'_id': trade['globalTradeID'],
  |                         }+
  |                      +{ }+,
  |                      +{ }+,
  |                      +{ }+
  |
  |
  |
  | # Built by tools.market.Market ===================
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
