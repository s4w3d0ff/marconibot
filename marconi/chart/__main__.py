if __name__ == '__main__':
    from . import Chart
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=4)
    from poloniex import Poloniex
    chart = Chart(pair='USDT_BTC', api=Poloniex(jsonNums=float))
    pp.pprint(chart())
