from binance import Client
from datetime import datetime, timezone, timedelta
from fetch_data import get_data
import pandas as pd
import time
from decimal import Decimal
import decimal
from dateutil import tz
from utils import TradingGraph, Write_to_file, Normalizing
from collections import deque
import numpy as np
from tensorflow.keras.optimizers import Adam
from main import CustomAgent
import json

api_key = "IkglEvMVJST0OmJA3Jfhi7nGUirfrYRnGsGdBTUoKNkpOPiDmSnfElk3zujUrabT"
secret_key = "hXOnb96VFSBSfvrHJYAdBv9UGR61CnbpqXZpDhoqGqc0QxbLNI9BdsCZsRrtyou2"
client = Client(api_key, secret_key)

def round_down(value, decimals):
    with decimal.localcontext() as ctx:
        d = decimal.Decimal(value)
        ctx.rounding = decimal.ROUND_DOWN
        return round(d, decimals)

def get_latest_price(symbol):
    tickers = client.get_all_tickers()
    price = None
    for ticker in tickers:
        if ticker['symbol'] == symbol:
             price = ticker["price"]
    assert price
    return Decimal(price)

def get_asset_balance(symbol):
    info = client.get_asset_balance(symbol)
    return round_down(Decimal(info["free"]), 5)

def get_net_worth(crypto, currency, price):
    curr = get_asset_balance(currency)
    crypto_qty = get_asset_balance(crypto)
    return round_down((curr + crypto_qty*price), 5)

def buy_all(symbol):
    amount = get_asset_balance("USDT")
    return buy(symbol, amount)

def buy(symbol, amount):
    order = client.create_order(symbol=symbol, side="BUY", type="MARKET", quoteOrderQty=amount)
    assert order["status"] == "FILLED"
    total_qty = sum([Decimal(val["qty"]) for val in order["fills"]])
    buy_price = (sum([Decimal(val["qty"]) * Decimal(val["price"]) for val in order["fills"]]))/total_qty
    return total_qty

def sell_all(symbol):
    qty = get_asset_balance(symbol[:-4])
    qty = round_down(qty, 5)
    return sell(symbol, qty)

def sell(symbol, qty):
    order = client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty)
    assert order["status"] == "FILLED"
    total_qty = sum([Decimal(val["qty"]) for val in order["fills"]])
    sell_price = (sum([Decimal(val["qty"]) * Decimal(val["price"]) for val in order["fills"]]))/total_qty
    return total_qty

def get_orders(startTime, delta=1):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = startTime.replace(tzinfo=from_zone)
    currentTime = utc.astimezone(to_zone)
    sinceThisDate = int(currentTime.strftime('%s'))*int(1000)
    untilThisDate = int((currentTime+timedelta(hours=delta)).strftime('%s'))*int(1000)
    orders = client.get_all_orders(symbol="BTCUSDT", startTime=sinceThisDate, endTime=untilThisDate)
    cryptoBought = 0
    cryptoSold = 0
    for order in orders:
        if order["side"] == "BUY":
            cryptoBought += Decimal(order["executedQty"])
        if order["side"] == "SELL":
            cryptoSold += Decimal(order["executedQty"])
    return cryptoBought, cryptoSold



class LiveTradindEnv:
    def __init__(self, lookback_window_size=100, Show_reward=False, Render_range=100, Show_indicators=False, normalize_value=40000, crypto="BTC", currency="USDT", initial_balance=1000):

        self.initial_balance = initial_balance
        self.lookback_window_size = lookback_window_size
        self.Show_reward = Show_reward # show order reward in rendered visualization
        self.Show_indicators = Show_indicators # show main indicators in rendered visualization
        self.normalize_value = (normalize_value*initial_balance)/1000
        self.Render_range = Render_range # render range in visualization
        self.crypto = crypto
        self.currency = currency
        self.tradePair = crypto + currency
        self.order_history = deque(maxlen=self.lookback_window_size)
        self.market_history = deque(maxlen=self.lookback_window_size)


    def reset(self, df):
        market_data = df.iloc[:, :14]
        market_data_nomalized = Normalizing(market_data[99:])[1:].dropna()
        market_data_nomalized = market_data_nomalized[100:].dropna()
        market_data_nomalized = market_data_nomalized.iloc[-self.lookback_window_size:,:]
        market_data_columns =  list(market_data_nomalized.columns[1:])

        order_data = df.iloc[:,14:]
        order_data = order_data.iloc[-self.lookback_window_size:,:]
        order_data_columns = list(order_data.columns[:])

        for ind, row in market_data_nomalized.iterrows():
            self.market_history.append([market_data_nomalized.loc[ind, column] for column in market_data_columns])

        for ind, row in order_data.iterrows():
            self.order_history.append([order_data.loc[ind, column]/self.normalize_value for column in order_data_columns])

        state = np.concatenate((self.order_history, self.market_history), axis=1)
        return state


    def step(self, action):

        balance  = get_asset_balance(self.currency)
        crypto_held = get_asset_balance(self.crypto)
        current_price = get_latest_price(self.crypto + self.currency)

        if action == 0:
            print ("Hold")
            pass

        elif action == 1 and balance > self.initial_balance*0.05:
            print ("Buying")

        elif action == 2 and crypto_held*current_price> self.initial_balance*0.05:
            print ("Selling")

        return None, 0, False


    def get_reward(self, close):
        pass


    def render(self, visualize = False):
        pass


def prefill_data(fileName, crypto, currency):
    print ("Prefilling data")
    tradePairSymbol = crypto + currency
    df = pd.read_csv(fileName)
    df = df.set_index('Date')
    currentTime = datetime.now(timezone.utc)
    lastTimeStampStr = list(df.index.values.tolist())[-1]
    lastTimeStamp = datetime.strptime(lastTimeStampStr, '%Y-%m-%d %H:%M:%S')
    new_df = get_data(tradePairSymbol, "1h", lastTimeStamp - timedelta(hours=150), currentTime - timedelta(hours=1))
    new_df = new_df.loc[lastTimeStampStr:]

    for ind, row in new_df.iterrows():
        crypto_bought, crypto_sold = get_orders(ind)
        balance = get_asset_balance(currency)
        net_worth = get_net_worth(crypto, currency, Decimal(row["Close"]))
        crypto_held = get_asset_balance(crypto)
        new_df.at[ind,'balance'] = balance
        new_df.at[ind,'net_worth'] = net_worth
        new_df.at[ind, 'crypto_bought'] = crypto_bought
        new_df.at[ind, 'crypto_sold'] = crypto_sold
        new_df.at[ind, 'crypto_held'] = crypto_held

    final_df = pd.concat([df, new_df.iloc[1: , :]])
    final_df.to_csv(fileName)



def scheduler(fileName, crypto, currency, modelFolderName, modelFileName):
    while (1):
        currentTime = datetime.now(timezone. utc)
        minute = currentTime.minute
        df = pd.read_csv(fileName)
        df = df.set_index('Date')
        currentTime = datetime.now(timezone. utc)
        lastTimeStampStr = list(df.index.values.tolist())[-1]
        lastTimeStamp = datetime.strptime(lastTimeStampStr, '%Y-%m-%d %H:%M:%S')
        if lastTimeStamp.hour != (currentTime.hour-1):

            with open(modelFolderName+"/Parameters.json", "r") as json_file:
                params = json.load(json_file)
            params["Actor name"] = f"{modelFileName}_Actor.h5"
            params["Critic name"] = f"{modelFileName}_Critic.h5"
            name = params["Actor name"][:-9]

            agent = CustomAgent(lookback_window_size=100, optimizer=Adam, depth=params["depth"], model=params["model"])
            agent.load(modelFolderName, modelFileName)

            prefill_data(fileName, crypto, currency)

            if (minute < 5):
                df = pd.read_csv(fileName)
                env = LiveTradindEnv(initial_balance=24)
                state = env.reset(df)
                action, prediction = agent.act(state)
                print(action)
                env.step(action)

        if minute < 5 or minute >= 58:
            time.sleep(1)
        else:
            sleep_time = (60-minute)*30
            assert (sleep_time > 0)
            assert (minute + sleep_time/60)<59
            print ("Current Time = %s,  Sleeping for %s minutes" % (currentTime, sleep_time/60))
            time.sleep(sleep_time)


fileName = "./test"
scheduler(fileName, "BTC", "USDT", "2022_02_05_20_27_Crypto_trader", "1387.91_Crypto_trader")
