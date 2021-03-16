import python_bitbankcc
from pprint import pprint
import configparser
import time
from datetime import datetime
import pandas as pd
import numpy as np
import requests
import json


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

#coingeckoのAPIから5分単位で価格を取得してデータフレームにする
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
        price = pd.Series(coin_data['prices'])
        #pandasで移動平均線を計算
        SMA5 = price.rolling(window=5).mean()
        SMA20 = price.rolling(window=20).mean()
        #コイン価格と2つの移動平均線の最新数値を取得
        reala5 = SMA5[len(SMA5)-2]
        realb5 = SMA5[len(SMA5)-1]
        reala20 = SMA20[len(SMA20)-2]
        realb20 = SMA20[len(SMA20)-1]

        if flag==True: 
            if reala5 < reala20 and realb5 > realb20: 
                prv_set.order(
                    PAIR,
                    str(price),
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
            time.sleep(600)
            prv_set.order(
                PAIR,
                str(price),
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