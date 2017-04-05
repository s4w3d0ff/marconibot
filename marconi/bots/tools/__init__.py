import logging
# html parser (for trollbox lurker)
try:
    from html.parser import HTMLParser
except:
    from HTMLParser import HTMLParser
# 3rd party
# - pip install pymongo
from pymongo import MongoClient
# - https://github.com/s4w3d0ff/trade_indica
import trade_indica as indica
#######################################################################
# tools logger
logger = logging.getLogger(__name__)

PHI = (1 + 5 ** 0.5) / 2
