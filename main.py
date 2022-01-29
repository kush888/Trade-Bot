from binance import Client
import pandas as pd
import talib as ta

api_key = "IkglEvMVJST0OmJA3Jfhi7nGUirfrYRnGsGdBTUoKNkpOPiDmSnfElk3zujUrabT"
secret_key = "hXOnb96VFSBSfvrHJYAdBv9UGR61CnbpqXZpDhoqGqc0QxbLNI9BdsCZsRrtyou2"
client = Client(api_key, secret_key)


def get_data(symbol, interval, lookback):
	frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback+' min ago UTC'))
	frame = frame.iloc[:,:6]
	frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
	frame = frame.set_index('Time')
	frame.index = pd.to_datetime(frame.index, unit='ms')
	frame = frame.astype(float)
	return frame


def apply_technicals(frame):
	frame['macd'], frame['signal'], frame['hist'] = ta.MACD(frame['Close'], 12, 26, 9)
	# frame['sma7'] = ta.SMA(frame['Close'], 7)
	# frame['sma25'] = ta.SMA(frame['Close'], 25)
	# frame['RSI'] = ta.RSI(frame['Close'], 14)
	# frame.dropna(inplace=True)
	return frame


def buy(symbol, qty):
	order = client.create_order(symbol=symbol, side="BUY", type="MARKET", quantity=qty )
	return order


def sell(symbol, qty):
	order = client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty)
	return order


def main():
	total_profit = 0
	open_position = False
	qty = 0.0004
	symbol = "BTCUSDT"
	while True:
		data = get_data(symbol, '1m', "45 ")
		data = apply_technicals(data)
		print (data.iloc[-1]['hist'], data.iloc[-2]['hist'], total_profit)
		if not open_position and data.iloc[-1]['hist'] > 0 and data.iloc[-2]['hist'] < 0:
			print ("BUY")
			open_position = True
			order = buy(symbol, qty)
			buy_price = float(order['fills'][0]['price'])
		elif open_position and data.iloc[-1]['hist'] < 0 and data.iloc[-2]['hist'] > 0:
			print ("SELL")
			open_position = False
			order = sell(symbol, qty)
			sell_price = float(order['fills'][0]['price'])
			profit = (sell_price - buy_price)*qty
			total_profit += profit
			print("Total Profit: ", total_profit, "Profit: ", profit)

main()

