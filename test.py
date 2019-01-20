#!/usr/bin/python3
import calendar
import ccxt
from datetime import datetime
import json
import matplotlib.pyplot as plt
from mpl_finance import candlestick2_ohlc,volume_overlay
import math
import numpy as np
import pandas as pd
import requests
#from scipy.stats import linregress
#import talib
import time

#price
def get_price(min,n):
    while True:
        try:
            now = datetime.utcnow()
            unixtime = calendar.timegm(now.utctimetuple())
            since = unixtime - p_time
            query = {"period": str(min),"after": str(since),"before": str(unixtime)}
            data = json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params=query).text)
            return { "time" : data["result"][str(min)][n][0],
                "open" : data["result"][str(min)][n][1],
                "high" : data["result"][str(min)][n][2],
	            "low" : data["result"][str(min)][n][3],
                "close" : data["result"][str(min)][n][4]},data
        except Exception as e:
            print("価格の取得に失敗しました(;_;)")
            print("error_code: " + str(e.args))
            time.sleep(10)
#DataFrame
def create_df():
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
    df['time_id'] = df.index + 1
    return df
#Technical
def EMA(EMA_period,old,new):
    df = create_df()
    alpha = 2/(EMA_period+1)
    df["ema"] = df['close'].ewm(alpha=alpha).mean()[-old:-new]
    return df["ema"]

def EMA_check(EMA_period): 
    UPtrend_angle = 1
    DWtrend_angle = -1
    NowAngle = 0
    for var in range(int(p_time/period)+1,2,-1):
        df = EMA(EMA_period,var,var-2)
        df_list = list(df.values.flatten())
        NowAngle = np.arctan((df_list[int(p_time/period)+2-var]-df_list[int(p_time/period)+1-var]))
        if NowAngle > UPtrend_angle:
            flag["trend"] = "buy"
        elif NowAngle < DWtrend_angle:
            flag["trend"] = "sell"
        else:
            flag["trend"] = None
    return df_list[int(p_time/period)-1]

def RSI():
    df = create_df()
    diff = df.diff()
    diff_data = diff[1:]
    up, down = diff_data.copy(), diff_data.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    up_sma_14 = up.rolling(window=14, center=False).mean()
    down_sma_14 = down.abs().rolling(window=14, center=False).mean()
    up_sma_14 = up.rolling(window=14, center=False).mean()
    down_sma_14 = down.abs().rolling(window=14, center=False).mean()
    RS = up_sma_14 / down_sma_14
    RSI = 100.0 - (100.0 / (1.0 + RS))
    return RSI

#order
def create_position(side):
    try:
        order = bitflyer.create_order(
            symbol = 'BTC/JPY',
            type='market',
            side= side,
            amount= lot,
            params = { "product_code" : "FX_BTC_JPY" })
        print("成行注文しました!!")
        if side == "buy":
            flag["message"] = data["close"]
        elif side == "sell":
            flag["message"] = data["close"]
        flag["position"] = side
        flag["order"] = True
        time.sleep(10)
        return flag
    except Exception as e:
        print("成行注文に失敗しました(;_;) : " + e.args)
        time.sleep(10)

def close_position(side):
    while True:
        try:
            order = bitflyer.create_order(
				symbol = 'BTC/JPY',
				type='market',
				side= side,
				amount= lot,
				params = { "product_code" : "FX_BTC_JPY" })
            print("成行決済しました!!")
            if side == "buy":
                flag["message"] = data["close"]
            elif side == "sell":
                flag["message"] = data["close"]
            flag["position"] = 0
            flag["order"] = False
            time.sleep(10)
            return flag
        except:
            print("成行決済に失敗しました(;_;)")
            time.sleep(10)

def check_order():
    if flag["order"] == True:
        if flag["position"] == 'buy':
            if short_tmp > EMA_check(long_EMA) > short_data and flag["trend"] == "sell":
                close_position("sell")
        elif flag["position"] == 'sell':
            if short_tmp < EMA_check(long_EMA) < short_data and flag["trend"] == "buy":
                close_position("buy")
    else:
        if short_tmp < EMA_check(long_EMA) < short_data and flag["trend"] == "buy" :
            create_position("buy")
        elif short_tmp > EMA_check(long_EMA) > short_data and flag["trend"] == "sell":
            create_position("sell")
        else:
            print("...............")

#=====================================================#

bitflyer = ccxt.bitflyer({
    
})
p_time = 60 * 60 * 24
short_EMA = 14
long_EMA = 25
period = 60
lot = "0.01"
flag = {
    'position': 0,
    'trend': 0,
    'order': 0,
    'message':0
}
tmp,full_data = get_price(period,-1)
short_tmp = EMA_check(short_EMA)
while True:
    data,full_data = get_price(period,-1)
    if tmp["time"] != data["time"]:
        short_data = EMA_check(short_EMA)
        check_order()
        tmp_short = short_data
        tmp = data
    time.sleep(10)

