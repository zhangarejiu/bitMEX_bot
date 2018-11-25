# @Date:   2018-11-19T22:34:49+09:00
# @Last modified time: 2018-11-21T00:18:39+09:00



import ccxt
import pandas as pd
import numpy as np
import time
import sys
import math
import datetime
from time import sleep

def getdata( timeframe, num ,symbol):

    # bitMEX使用宣言
    bitmex = ccxt.bitmex()
    # テストネット使用宣言（本番時はコメントアウトする）
    bitmex.urls["api"] = bitmex.urls["test"]

    # タイムスタンプ取得
    time = bitmex.fetch_ticker(symbol=symbol)["timestamp"]

    # どの時間のローソク足のデータを取得したいかで処理分け
    if "1d" == timeframe:
        msec = 24 * 60 * 60 * 1000
    elif "4h" == timeframe:
        msec = 4 * 60 * 60 * 1000
    elif "1h" == timeframe:
        msec = 60 * 60 * 1000
    elif "30m" == timeframe:
        msec = 30 * 60 * 1000
    elif "15m" == timeframe:
        msec = 15 * 60 * 1000
    elif "5m" == timeframe:
        msec = 5 * 60 * 1000
    elif "3m" == timeframe:
        msec = 3 * 60 * 1000
    elif "1m" == timeframe:
        msec = 1 * 60 * 1000
    else:
        return "error"

    time = time - num * msec

    # ローソク足のデータ取得
    candles = bitmex.fetch_ohlcv(symbol=symbol, timeframe = timeframe, since = time)
    df = pd.DataFrame(candles,columns=['timeframe', 'open', 'high', 'low' ,'close', 'volume'])


    return df,msec/1000


def read_date(x):
    return datetime.datetime.fromtimestamp(x/1000)

def setdata(num):
    df18,sec = getdata(timeframe,num ,symbol1 )
    df19,sec = getdata(timeframe,num ,symbol2 )
    df = df18 - df19
    df['timeframe'] = df18['timeframe']
    #時間を可視化
    df['timeframe'] = df['timeframe'].apply(read_date)
    return df


# 単純移動平均（SMA）を取得する関数
#上記のdfデータフレーム
#numいくつの平均を求めるか
def getMA( df,num ):

    tmp = []
    avg = np.array([])
    for i in range(len(df) - num + 1):
        for j in range(num):
            #print(df['Close'][i+j])
            tmp.append( df['close'][i+j])

         # 平均値計算
        value = np.average(tmp)
        avg = np.append(avg,value)
        tmp = []

    return avg

def getSTD( df,num ):

    tmp = []
    std = np.array([])
    for i in range(len(df) - num + 1):
        for j in range(num):
            #print(df['Close'][i+j])
            tmp.append( df['close'][i+j])

         # 平均値計算
        value = np.std(tmp)
        std = np.append(std,value)
        tmp = []

    return std

def bitmex(): #CCXT を呼び出す関数

   bitmex = ccxt.bitmex({
    #APIキーを自分のものに差し替える
    "apiKey": "",
    "secret": ""
       })

   bitmex.urls['api'] = bitmex.urls['test'] #テスト用 本番口座の場合は不要

   return bitmex

#口座情報の取得
balance = bitmex().fetch_balance()
print(balance)



timeframe = "1m"
num = 5
symbol1 = 'XBTZ18'
symbol2 = 'XBTH19'
#5単位前までのデータを取得
df18,sec = getdata(timeframe,num ,symbol1 )
df19,sec = getdata(timeframe,num ,symbol2 )
df = df18 - df19
df['timeframe'] = df18['timeframe']
print(df)
#時間を可視化
df['timeframe'] = df['timeframe'].apply(read_date)

#移動平均線、標準偏差を作成
df2 = df.copy()
MA5 = getMA(df,5)
STD5 = getSTD(df,5)
zero5 = np.zeros(num-1,dtype = float )
MA5 = np.insert(MA5, 0, zero5)
STD5 = np.insert(STD5, 0, zero5)
df2['bbd_p2'] = MA5 + (STD5 * 2)
df2['bbd_m2'] = MA5 - (STD5 * 2)

def limit(symbol,side, price, size):
    return bitmex().create_order(symbol, type='limit', side=side, price=price, amount=size)

def market(symbol,side, size):
    return bitmex().create_order(symbol, type='market', side=side, amount=size)

#ここまでで一通りの動作確認完了。以下実装
LOT = 2 #発注数(単位:XBTZ18 or XBTH19)
CLOSE_RANGE = STD5[len(STD5)-1]#利確幅(単位:XBTZ18 or XBTH19)
STOP_RANGE = STD5[len(STD5)-1]*2 #損切り幅(単位:XBTZ18 or XBTH19)

def trade(symbol,order_name, LOT):
    try:
        order = market(symbol,order_name, LOT)
        print('Entry: ' + order['info']['ordType'] + ' ' + order['info']['side'] + ': ' + str(order['info']['orderQty']) + ' @ ' + str(order['info']['price']) + ' / ' + order['id'])

        if len(order) == 0:
            print('No Position'+' {0} {1}'.format(symbol,order_name))

        if len(order) != 0:
            return -1,order

        if (order_name == 'buy') & (len(order) != 0):
            return -1,order
        elif (order_name == 'sell') & (len(order) != 0):
            return -1,order

    except Exception as error:
        print(error)
        print('Please,change LOT or EntryPrice')
        return 0,0
        pass


old = time.time()
old_count = 0
sig = 10
order_fin1 = 0
order_fin2 = 0
order_fin3 = 0
order_fin4 = 0


#flagは一連の注文がセットで通るために必要
#同じ注文を繰り返さないため
print("############BOT strats!!!##############")

while True:
    last = bitmex().fetch_ticker(symbol1)['last'] - bitmex().fetch_ticker(symbol2)['last']
    print('LTP: ' + str(last))

    if bitmex().private_get_position()[0]['currentQty'] == 0:
        print('No Position')

    flag1 = 1
    flag2 = 1

    if (flag1 == -1)&(flag2 == -1):
        flag1 = 1
        flag2 = 1

    elif df2['bbd_p2'][len(df)-1] - STD5[len(STD5)-1]/sig < last < df2['bbd_p2'][len(df)-1] + STD5[len(STD5)-1]/sig:
        if  flag1 == 1:
            flag1,order1 = trade(symbol=symbol1,order_name='sell', LOT=LOT)
        if  flag2 == 1:
            flag2,order2 = trade(symbol=symbol2,order_name='buy',  LOT=LOT)

    elif (flag1 == -1)&(flag2 == -1):
        flag1 = 1
        flag2 = 1

    elif df2['bbd_m2'][len(df)-1] - STD5[len(STD5)-1]/sig < last < df2['bbd_m2'][len(df)-1] + STD5[len(STD5)-1]/sig:
        if  flag1 == 1:
            flag1,order3 = trade(symbol=symbol1,order_name='buy', LOT=LOT)
        if  flag2 == 1:
            flag2,order4 = trade(symbol=symbol2,order_name='sell',LOT=LOT)
###############################################################################
#データの取得

    now = time.time()
    count = math.floor((now - old)/sec)
    a = count - old_count
    if a>= 1:
        old_count = count
        dfsample = setdata(num=2)
        df = pd.concat([df,dfsample])
        df = df.drop_duplicates()
        df = df.dropna()
        df = df.reset_index()
        df = df.drop("index", axis=1)
#         print('df')
#         print(df)
        #データの作成
        df2 = df.copy()
        MA5 = getMA(df,5)
        STD5 = getSTD(df,5)
        zero5 = np.zeros(num-1,dtype = float )
        MA5 = np.insert(MA5, 0, zero5)
        STD5 = np.insert(STD5, 0, zero5)
        df2['bbd_p2'] = MA5 + (STD5 * 2)
        df2['bbd_m2'] = MA5 - (STD5 * 2)
        print('df2')
        print(df2)


    ########################################################################


    if last > df2['bbd_p2'][len(df)-1] + STOP_RANGE:
        #損切り
        LOT1 = bitmex().private_get_position()[0]['currentQty']
        LOT2 = bitmex().private_get_position()[1]['currentQty']
        if LOT1 != 0:
            flag1,order_fin1 = trade(symbol=symbol1,order_name='buy', LOT=LOT1)
        if LOT2 != 0:
            flag2,order_fin2 = trade(symbol=symbol2,order_name='sell', LOT=LOT2)
        if len(order_fin1)*len(order_fin2) != 0:
            print('Loss Cut 2!!')
            sys.exit()

#     if last < df2['bbd_p2'][len(df)-1] - CLOSE_RANGE:
#         #利益確定
#         LOT1 = bitmex().private_get_position()[0]['currentQty']
#         LOT2 = bitmex().private_get_position()[1]['currentQty']
#         if LOT1 != 0:
#             flag1,order_fin1 = trade(symbol=symbol1,order_name='buy', LOT=LOT1)
#         if LOT2 != 0:
#             flag2,order_fin2 = trade(symbol=symbol2,order_name='sell', LOT=LOT2)
#         if len(order_fin1)len(order2_fin2) != 0:
#         print('Close!!')
#         sys.exit()


    if last < df2['bbd_m2'][len(df)-1] - STOP_RANGE:
        #損切り
        LOT1 = bitmex().private_get_position()[0]['currentQty']
        LOT2 = bitmex().private_get_position()[1]['currentQty']
        if LOT1 != 0:
            flag3,order_fin3 = trade(symbol=symbol1,order_name='sell', LOT=LOT1)
        if LOT2 != 0:
            flag4,order_fin4 = trade(symbol=symbol2,order_name='buy', LOT=LOT2)
        if len(order_fin3)*len(order_fin4) != 0:
            print('Loss Cut 2!!')
            sys.exit()

#     if last > df2['bbd_m2'][len(df)-1] + CLOSE_RANGE:
#         #利益確定
#         LOT1 = bitmex().private_get_position()[0]['currentQty']
#         LOT2 = bitmex().private_get_position()[1]['currentQty']
#         if LOT1 != 0:
#             flag3,order_fin3 = trade(symbol=symbol1,order_name='sell', LOT=LOT1)
#         if LOT2 != 0:
#             flag4,order_fin4 = trade(symbol=symbol2,order_name='buy', LOT=LOT2)
#         if len(order_fin3)len(order_fin4) != 0:
#         print('Close!!')
#         sys.exit()

    #sleep(sec/10)
