from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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

def fetch_twse_realtime(stock_code, retries=3, delay=2):
    import time
    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    params = {"ex_ch": f"tse_{stock_code}.tw", "json": "1", "delay": "0"}
    for _ in range(retries):
        response = requests.get(url, params=params)
        data = response.json()
        if "msgArray" in data and len(data["msgArray"]) > 0:
            stock_info = data["msgArray"][0]
            last_price = stock_info.get('z')
            if last_price != "-":
                return float(last_price)
        time.sleep(delay)
    print("Failed to fetch valid real-time data after retries.")
    return stock_info.get('o')

def calculate_k_values(data, period=9, alpha=1/3):
    data["High 9-day"] = data["High"].rolling(period).max()
    data["Low 9-day"] = data["Low"].rolling(period).min()
    data["RSV"] = (data["Close"] - data["Low 9-day"]) / (data["High 9-day"] - data["Low 9-day"]) * 100

    # Initial K value set to 50
    data["K"] = data["RSV"].ewm(alpha=alpha, adjust=False).mean()
    return data

def plot_data(data, stock_code):
    # 转换日期为 Pandas 时间戳格式
    # data = data.dropna(ignore_index=True)
    data = data.dropna().reset_index(drop=True)
    # print(data)
    plt.figure(figsize=(12, 6))

    # Add main title for the plot
    plt.suptitle(f"Stock Code: {stock_code}", fontsize=16)

    # First subplot：每天收盘价和区间
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(data["Date"], data["Close"], label="Close Price", color="blue")
    
    # Add high and low interval as rectangles
    for i, row in data.iterrows():
        rect = Rectangle((i-0.4, row["Low"]), 0.8, row["High"] - row["Low"], color='gray', alpha=0.3)
        ax1.add_patch(rect)
        ax1.text(i+0.2, row["Close"]+0.2, f'{row["Close"]:.2f}', ha='center', color='red')

    ax1.set_title("Daily Closing Price with High-Low Range")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Price")
    ax1.grid()
    ax1.legend()

    # 第二张图：每天 K 值
    ax2 = plt.subplot(2, 1, 2)
    ax2.plot(data["Date"], data["K"], label="K Value", color="green")
    ax2.axhline(20, color='red', linestyle='--', alpha=0.2, label= None)  # Add K=20 line
    ax2.axhline(80, color='red', linestyle='--', alpha=0.2, label= None)  # Add K=80 line
    ax2.set_title("Daily K Value")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("K Value")
    ax2.grid()
    ax2.legend()

    # Ensure the x axis of the second plot matches that of the first plot
    ax2.set_xlim(ax1.get_xlim())

    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


stock_code = "0050"

now = datetime.now()
current_month = now.strftime("%Y%m")
last_month = (now - relativedelta(months=1)).strftime("%Y%m")

current_month_data = fetch_twse_history(stock_code, current_month+"01") 
last_month_data = fetch_twse_history(stock_code, last_month+"01") 
history_data = pd.concat([last_month_data, current_month_data], ignore_index=True)
# print(history_data)

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

plot_data(history_data, stock_code)
