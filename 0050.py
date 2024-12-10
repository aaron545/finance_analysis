from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests
import pandas as pd

def fetch_twse_history(stock_code, date): # date format is "yyyymm01"
    url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
    params = {"response": "json", "date": date, "stockNo": stock_code}
    response = requests.get(url, params=params)
    data = response.json()

    if data["stat"] == "OK":
        df = pd.DataFrame(
            data["data"], 
            columns=["Date", "Volume", "Turnover", "Open", "High", "Low", "Close", "Price Change", "Transactions"]
        )
        df[["High", "Low", "Close"]] = df[["High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce")
        return df[["Date","High", "Low", "Close"]]
    else:
        print("Failed to fetch historical data:", data["stat"])
        return None

def fetch_twse_realtime(stock_code):
    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    params = {"ex_ch": f"tse_{stock_code}.tw", "json": "1", "delay": "0"}
    response = requests.get(url, params=params)
    data = response.json()

    if "msgArray" in data and len(data["msgArray"]) > 0:
        stock_info = data["msgArray"][0]
        current_price = float(stock_info['z'])  # 現價
        return current_price
    else:
        print("即時數據獲取失敗")
        return None

def calculate_k_values(data, period=9, alpha=1/3):
    data["High 9-day"] = data["High"].rolling(period).max()
    data["Low 9-day"] = data["Low"].rolling(period).min()
    data["RSV"] = (data["Close"] - data["Low 9-day"]) / (data["High 9-day"] - data["Low 9-day"]) * 100

    # Initial K value set to 50
    data["K"] = data["RSV"].ewm(alpha=alpha, adjust=False).mean()
    return data



stock_code = "0050"

now = datetime.now()
current_month = now.strftime("%Y%m")
last_month = (now - relativedelta(months=1)).strftime("%Y%m")

current_month_data = fetch_twse_history(stock_code, current_month+"01") 
last_month_data = fetch_twse_history(stock_code, last_month+"01") 
history_data = pd.concat([last_month_data, current_month_data], ignore_index=True)

current_date = now.strftime("%m/%d")
taiwan_year = now.year - 1911
now_date = f"{taiwan_year}/{current_date}"

if history_data.tail(1)["Date"].iloc[0] != now_date:
	current_price = fetch_twse_realtime(stock_code)
	new_row = {
                "Date": now_date,
                "High": float(current_price),
                "Low": float(current_price),
                "Close": float(current_price),
            }
	history_data = pd.concat([history_data, pd.DataFrame([new_row])], ignore_index=True)

history_data = calculate_k_values(history_data)
print(round(history_data["K"].tail(1).iloc[0], 2))