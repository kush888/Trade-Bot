from binance import Client
import pandas as pd
import talib as ta

api_key = "IkglEvMVJST0OmJA3Jfhi7nGUirfrYRnGsGdBTUoKNkpOPiDmSnfElk3zujUrabT"
secret_key = "hXOnb96VFSBSfvrHJYAdBv9UGR61CnbpqXZpDhoqGqc0QxbLNI9BdsCZsRrtyou2"
client = Client(api_key, secret_key)


def get_data(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + ' min ago UTC'))
    frame = frame.iloc[:, :6]
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
    order = client.create_order(symbol=symbol, side="BUY", type="MARKET", quantity=qty)
    return order


def sell(symbol, qty):
    order = client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty)
    return order


def shouldBuy(prevPrice, currPrice, threshold):
    return ((prevPrice - currPrice) / prevPrice) * 100 > threshold


def shouldSell(prevPrice, currPrice, threshold):
    return ((prevPrice - currPrice) / prevPrice) * 100 < -threshold


def main():
	threshold = 0.5
	symbol = "SOLUSDT"
	baseQty = 10
	crypto_holding = baseQty/5
	data = get_data(symbol, '1m', "1 ")
	initial_price = data.iloc[-1]["Close"]
	balance = initial_price*crypto_holding
	initial_value = initial_price*crypto_holding + balance
	prevPrice = initial_price
	print ("INITIAL PRICE: ", initial_price, "INITIAL VALUE: ", initial_value)
	it = -1
	while True:
		data = get_data(symbol, '1m', "45 ")
		currPrice = data.iloc[-1]["Close"]
		if shouldBuy(prevPrice, currPrice, threshold):
			buyQty = ((prevPrice - currPrice) / prevPrice) * baseQty * 20
			balance = balance - (buyQty * currPrice) - (buyQty * currPrice * 0.001)
			crypto_holding += buyQty
			print("Bought %s %s at %s price of value %s" % (buyQty, symbol, currPrice, buyQty*currPrice))
			prevPrice = currPrice
			continue
		if shouldSell(prevPrice, currPrice, threshold):
			sellQty = ((prevPrice - currPrice) / prevPrice) * baseQty * 20
			balance = balance - (sellQty * currPrice) - (-sellQty * currPrice * 0.001)
			crypto_holding += sellQty
			print("Sold %s %s at %s price of value %s" % (-sellQty, symbol, currPrice, sellQty*currPrice))
			prevPrice = currPrice
			continue

		it += 1
		if it % 50 == 0:
			portfolioBalance = currPrice*crypto_holding + balance
			print("QTY: ", crypto_holding, "Cash: ", balance, "Portfolio Balance: ", portfolioBalance, "Profit: ", portfolioBalance - initial_value, "Previous Price: ", prevPrice, "CurrentPrice: ", currPrice, "Target Price: ", prevPrice*(1+threshold/100), prevPrice*(1-threshold/100),"Expected Return: ", balance+crypto_holding*initial_price - initial_value)
main()
