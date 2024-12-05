import yfinance as yf

TW_0050 = yf.Ticker("0050.TW")

data = TW_0050.history(period='1mo')[['Open', 'High', 'Low', 'Close']]
print(data)

k_period = 14

data['High_k'] = data['High'].rolling(window=k_period).max()
data['Low_k'] = data['Low'].rolling(window=k_period).min()

data['K'] = (data['Close'] - data['Low_k']) / (data['High_k'] - data['Low_k']) * 100

print(data)