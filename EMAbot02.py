#!/usr/bin/python3
import calendar
import ccxt
from datetime import datetime
import json
import numpy as np
import pandas as pd 
import requests
import time

def get_price(min,n):
    try:
        now = datetime.utcnow()
        unixtime = calendar.timegm(now.utctimetuple())
        since = unixtime - 60 * 60
        query = {"period": str(min),"after": str(since),"before": str(unixtime)}
        data = json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params=query).text)
        return { "close_time" : data["result"][str(min)][n][0],
                "open_price" : data["result"][str(min)][n][1],
                "high_price" : data["result"][str(min)][n][2],
		        "low_price" : data["result"][str(min)][n][3],
                "close_price": data["result"][str(min)][n][4]},data
    except Exception as e:
        print(e.args)
        time.sleep(10)

def create_position(side):
    try:
        order = bitflyer.create_order(
            symbol = 'BTC/JPY',
            type='market',
            side= side,
            amount= str(lot),
            params = { "product_code" : "FX_BTC_JPY" })
        print("成行注文しました!!")
        flag["position"] = side
        time.sleep(10)
        return flag
    except:
        print("成行注文に失敗しました(;_;)")

def close_position(side):
    while True:
        try:
            order = bitflyer.create_order(
				symbol = 'BTC/JPY',
				type='market',
				side= side,
				amount= str(lot),
				params = { "product_code" : "FX_BTC_JPY" })
            print("成行決済しました!!")
            flag["position"] = 0
            time.sleep(10)
            return flag
        except:
            print("成行決済に失敗しました(;_;)")
            time.sleep(10)

def EMA(EMA_period,period):
    for n in [str(period)]:
        row = full_data["result"][str(n)]
        df = pd.DataFrame(row,
                        columns=['exectime', 
                                'open', 
                                'high', 
                                'low', 
                                'close', 
                                'price', 
                                'volume'])
    alpha = 2/(EMA_period+1)
    ema = df['close'].ewm(alpha=alpha).mean()[-1:]
    return int(ema.values[0])

def check_order():
    if flag["position"] == 'buy':
        if EMA(long_EMA,period) < EMA(short_EMA,period) and EMA(long_EMA,period) > tmp_EMA:
            close_position("sell")
    elif flag["position"] == 'sell':
        if EMA(long_EMA,period) > EMA(short_EMA,period) and EMA(long_EMA,period) < tmp_EMA:
            close_position("buy")
    elif flag["position"] == 0:
        if EMA(long_EMA,period) < EMA(short_EMA,period) and EMA(long_EMA,period) > tmp_EMA:
            create_position("buy")
        elif EMA(long_EMA,period) > EMA(short_EMA,period) and EMA(long_EMA,period) < tmp_EMA:
            create_position("sell")

#=====================================================#

bitflyer = ccxt.bitflyer({
    'apiKey':'',
    'secret':''
})
#EMAの期間
short_EMA = 14
long_EMA = 25
#何分足
period = 60
#枚数
lot = 0.2
flag = {
    'position': 0
}

tmp,full_data = get_price(period,-2)
tmp_EMA = EMA(short_EMA,period)
while True:
    data,full_data = get_price(period,-2)
    if data["close_time"] != tmp["close_time"]:
        check_order()
    tmp_EMA =  EMA(short_EMA,period)
    tmp = data
    time.sleep(10)
