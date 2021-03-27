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


conf = configparser.ConfigParser()
conf.read('config.ini')

API_KEY = conf['bitbank']['api_key']
API_SECRET = conf['bitbank']['api_secret']
PAIR = 'qtum_jpy'
AMOUNT = 1

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

#coingeckoのAPIから1時間単位で価格を取得してデータフレームにする
def get_price(ticker, term):
    url = ('https://api.coingecko.com/api/v3/coins/') + ticker + ('/market_chart?vs_currency=jpy&days=') + term
    r = requests.get(url)
    r2 = json.loads(r.text)
    s = pd.DataFrame(r2['prices'])
    s.columns = ['date', 'prices']
    date = []
    for i in s['date']:
        tsdate = int(i / 1000)
        loc = datetime.utcfromtimestamp(tsdate)
        date.append(loc)
    s.index = date
    del s['date']
    return s

def main():
    pub_set = BitBankPubAPI()
    prv_set = BitBankPrbAPI()

    flag = True

    while True:
        #コインの価格データ取得
        coin_data = get_price('qtum', '1')
        #price = pd.Series(coin_data['prices'])
        price = np.array(coin_data['prices'])
        #各インディゲーターの計算
        short_EMA = talib.EMA(price,timeperiod=8)
        long_EMA = talib.EMA(price,timeperiod=18)
        #RSI = talib.RSI(df_np,timeperiod=14)
        #upper, middle, lower = talib.BBANDS(df_np, timeperiod=25, nbdevup=2, nbdevdn=2, matype=0)

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
                print(d.strftime("%Y-%m-%d %H:%M:%S"), 'buy coin') 
            else: 
                d = datetime.today()
                print(d.strftime("%Y-%m-%d %H:%M:%S"), 'no trade')
        elif flag==False: 
            if long_EMA[-2] < short_EMA[-2] and long_EMA[-1] > short_EMA[-1]:
                prv_set.order(
                    PAIR,
                    str(price), #使われない
                    str(AMOUNT),
                    'sell',
                    'market'
                ) 
                flag= True 
                d = datetime.today() 
                print(d.strftime("%Y-%m-%d %H:%M:%S"), 'sell coin')
        time.sleep(300)

if __name__ == '__main__':
    main()