import python_bitbankcc
from pprint import pprint
import configparser
import time
from datetime import datetime
import pandas as pd
import numpy as np
import requests
import json
import talib
import matplotlib.pyplot as plt

conf = configparser.ConfigParser()
conf.read('config.ini')

API_KEY = conf['bitbank']['api_key']
API_SECRET = conf['bitbank']['api_secret']
PAIR = 'qtum_jpy'
AMOUNT = 10
samples = 30
interval_sec = 900

class BitBankPubAPI:

    def __init__(self):
        self.pub = python_bitbankcc.public()

    def get_ticker(self, pair):
        try:
            value = self.pub.get_ticker(pair)
            return value
        except Exception as e:
            print(e)
            return None

class BitBankPrbAPI:

    def __init__(self):
        self.prv = python_bitbankcc.private(API_KEY, API_SECRET)

    def get_asset(self):
        try:
            value = self.prv.get_asset()
            return value
        except Exception as e:
            print(e)
            return None

    def order(self, pair, price, amount, side, order_type):
        try:
            value = self.prv.order(pair, price, amount, side, order_type)
            return value
        except Exception as e:
            print(e)
            return None

pub_set = BitBankPubAPI()
prv_set = BitBankPrbAPI()

#bitbankから価格を取得
def get_price(how_many_samples):
    print("まずは今から"+str(how_many_samples*interval_sec)+"秒間、価格データを収集します。")
    price_list = []
    for i in range(how_many_samples):
        price = pub_set.get_ticker(PAIR)
        price_list.append(price['last'])
        time.sleep(interval_sec)

    print("収集が完了しました。")
    return price_list

def plot_profits(profit_list):
    today = datetime.today().strftime("%Y-%m-%d %H")
    fig = plt.figure()
    plt.plot(profit_list)
    plt.title('Total Profit')
    plt.xlabel('trade count')
    plt.ylabel('profit')
    #plt.show()
    fig.savefig(today + '.png')
    print('###Trade result saved###')

def main():
    #コインの価格データ取得
    coin_data = pd.DataFrame()
    coin_data['prices'] = get_price(samples)
    flag = True
    buy_price = sell_price = profit = timecount = 0
    profit_list = [0]
    while True:
        price_now = pub_set.get_ticker(PAIR)
        coin_data = coin_data.append({'prices': price_now['last']}, ignore_index=True)
        #price = pd.Series(coin_data['prices'])
        price = np.array(coin_data['prices'], dtype='float')
        #各インディゲーターの計算
        short_EMA = talib.EMA(price,timeperiod=6)
        long_EMA = talib.EMA(price,timeperiod=16)
        #RSI = talib.RSI(df_np,timeperiod=14)
        upper, middle, lower = talib.BBANDS(price, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

        if flag==True: 
            if long_EMA[-2] > short_EMA[-2] and long_EMA[-1] < short_EMA[-1]: 
                prv_set.order(
                    PAIR,
                    str(price), #使われない
                    str(AMOUNT),
                    'buy',
                    'market'
                )
                flag=False 
                d = datetime.today()
                buy_price = price[-1] * AMOUNT
                print(d.strftime("%Y-%m-%d %H:%M:%S"), 'buy coin') 
            else: 
                d = datetime.today()
                print(d.strftime("%Y-%m-%d %H:%M:%S"), 'no trade')
        elif flag==False: 
            if (long_EMA[-2] < short_EMA[-2] and long_EMA[-1] > short_EMA[-1]) or (price[-1] > upper[-1]):
                prv_set.order(
                    PAIR,
                    str(price), #使われない
                    str(AMOUNT),
                    'sell',
                    'market'
                ) 
                flag= True 
                d = datetime.today() 
                sell_price = price[-1] * AMOUNT
                profit += sell_price - buy_price
                profit_list.append(profit)
                print(d.strftime("%Y-%m-%d %H:%M:%S"), 'sell coin')
        coin_data.drop(coin_data.index[0], inplace=True)
        #coin_data.reset_index(drop=True, inplace=True)
        time.sleep(interval_sec)
        timecount += 1
        if timecount == 96:
            timecount = 0
            plot_profits(profit_list)

if __name__ == '__main__':
    main()