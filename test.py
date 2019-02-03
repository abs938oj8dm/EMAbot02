#!/usr/bin/python3
import calendar
import ccxt
from datetime import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import time
from pprint import pprint

#price
def create_df(min,i):
    while True:
        try:
            now = datetime.utcnow()
            unixtime = calendar.timegm(now.utctimetuple())
            since = unixtime - 60 * 60 * 3
            query = {"period": str(min),"after": str(since),"before": str(unixtime)}
            data = json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params=query).text)
            ticker = bitflyer.fetch_ticker('BTC/JPY', params = { "product_code" : "FX_BTC_JPY" })
            for n in [str(min)]:
                row = data["result"][str(n)]
                df = pd.DataFrame(row,
                                columns=['time',
                                        'open',
                                        'high', 
                                        'low', 
                                        'close', 
                                        'price', 
                                        'volume'])
            df['time_id'] = df.index + 1
            return {"time" : data["result"][str(min)][i][0],
                "open" : data["result"][str(min)][i][1],
                "high" : data["result"][str(min)][i][2],
		        "low" : data["result"][str(min)][i][3],
                "close": data["result"][str(min)][i][4],
                "price": data["result"][str(min)][i][5],
                "volume": data["result"][str(min)][i][6]},ticker,df

        except Exception as e:
            print("価格の取得に失敗しました(;_;)")
            print("error_code: " + str(e.args))
            time.sleep(10)
#Technical
def SMA(df,EMA_period):
    df["sma"] = df['close'].rolling(EMA_period).mean()
    return df["sma"]

def EMA(df,EMA_period):
    alpha = 2/(EMA_period+1)
    df["ema"] = df['close'].ewm(alpha=alpha).mean()
    return df["ema"]

def STD(df,EMA_period):
    alpha = 2/(EMA_period+1)
    df["std"] = df['close'].ewm(alpha=alpha).std()
    return df["std"]

def BBAND():
    mean = EMA(df,14)
    sigma = STD(df,14)
    #plus_sigma1 = round(mean + sigma)
    #minus_sigma1 = round(mean - sigma)
    plus_sigma2 = round(mean + 2*sigma)
    minus_sigma2 = round(mean - 2*sigma)

    return plus_sigma2,minus_sigma2

def DONCHAN(df,ticker):
    highest = max(df["high"])
    if ticker["last"] > int(highest):
        return {"side":"buy","price":highest}
    lowest = min(df["low"])
    if ticker["last"] < int(lowest):
        return {"side":"sell","price":lowest}
    return {"side" : None , "price":0}
#order
def create_Mpos(side):
    try:
        order = bitflyer.create_order(
            symbol = 'BTC/JPY',
            type='market',
            side= side,
            amount= "0.01",
            params = { "product_code" : "FX_BTC_JPY" })
        print("成行注文しました!!")
        flag["position"]["side"] = side
        flag["position"]["price"] = data["close"]
        time.sleep(10)
        return flag
    except Exception as e:
        print("成行注文に失敗しました(;_;) : " + e.args)
        time.sleep(10)

def close_Mpos(side):
    while True:
        try:
            order = bitflyer.create_order(
				symbol = 'BTC/JPY',
				type='market',
				side= side,
				amount= "0.01",
				params = { "product_code" : "FX_BTC_JPY" })
            print("成行決済しました!!")
            flag["position"]["side"] = 0
            flag["position"]["price"] = 0
            time.sleep(10)
            return flag
        except:
            print("成行決済に失敗しました(;_;)")
            time.sleep(10)
    
def close_Lpos(side,price):
    while True:
        try:
            order = bitflyer.create_order(
				symbol = 'BTC/JPY',
                type='limit',
                side=side,
	            price=price,
				amount= "0.01",
				params = { "product_code" : "FX_BTC_JPY" })
            print("指値決済しました!!")
            flag["position"]["side"] = 0
            flag["position"]["price"] = 0
            time.sleep(10)
            return flag
        except:
            print("指値決済に失敗しました(;_;)")
            time.sleep(10)

def check_positions():
    while True:
        try:
            size = []
            price = []
            positions = bitflyer.private_get_getpositions( params = { "product_code" : "FX_BTC_JPY" })
            if not positions:
                flag["position"]["side"] = 0
            for pos in positions:
                size.append(pos["size"])
                price.append(pos["price"])
                side = pos["side"]
			# 平均建値を計算する
            average_price = round(sum( price[i] * size[i] for i in range(len(price)) ) / sum(size))
            sum_size = round(sum(size),2)
            return {"average" : average_price, "price" : sum_size, "side" : side}
        except ccxt.BaseError as e:
            print("BitflyerのAPIで問題発生 : ",e)
            print("20秒待機してやり直します")
            time.sleep(20)

def check_signal(sp2,sm2,old_p,new_p,df):
    signal = DONCHAN(df,ticker)
    if flag["position"]["side"] == 0:
        if signal["side"] == "buy":
            create_Mpos("buy")
            close_Lpos("sell",ticker["close"] - 500)

        elif signal["side"] == "sell":
            create_Mpos("sell")
            close_Lpos("buy",ticker["close"] + 500)

    elif flag["position"]["side"] == "buy":
        if signal["side"] == "sell":
            close_Mpos("sell")
        else:
            check_positions()
        
    elif flag["position"]["side"] == "sell":
        if signal["side"] == "buy":
            close_Mpos("buy")
        else:
            check_positions()
        
#=====================================================#

bitflyer = ccxt.bitflyer({
    'apiKey':'',
    'secret':''
})
period = 60
flag = {
    'position':{
        'side': 0,
        'price': 0,
    },
    'trend': 0,
}

while True:
    data,ticker,df = create_df(60,-1)
    sp2,sm2 = BBAND()
    check_signal(sp2,sm2,data,ticker["last"],df)
    time.sleep(10)
