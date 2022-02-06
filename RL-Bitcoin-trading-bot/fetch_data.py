from binance import Client
import pandas as pd
import datetime
from ta.trend import SMAIndicator
from ta.trend import SMAIndicator, macd, PSARIndicator
from ta.volatility import BollingerBands
from ta.momentum import rsi
from indicators import *



api_key = "IkglEvMVJST0OmJA3Jfhi7nGUirfrYRnGsGdBTUoKNkpOPiDmSnfElk3zujUrabT"
secret_key = "hXOnb96VFSBSfvrHJYAdBv9UGR61CnbpqXZpDhoqGqc0QxbLNI9BdsCZsRrtyou2"
client = Client(api_key, secret_key)


def get_data(symbol, interval, sinceThisDate, untilThisDate):
    df = pd.DataFrame(client.get_historical_klines(symbol, interval, str(sinceThisDate), str(untilThisDate)))
    df = df.iloc[:, :6]
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype(float)
    df["Date"] = pd.to_datetime(df["Date"], unit='ms')
    df = df.sort_values('Date')
    df = AddIndicators(df)
    df = df.dropna()
    df = df.set_index('Date')
    return df


if __name__ == "__main__":
    years=6
    symbol = "BTCUSDT"
    timeframe = "1h"
    untilThisDate = datetime.datetime.now()
    sinceThisDate = datetime.datetime.now() - datetime.timedelta(days=365*years)
    df = get_data(symbol, timeframe, sinceThisDate, untilThisDate)
    fileName = "%s years %s interval %s data" % (years, timeframe, symbol)
    df.to_csv(fileName)

