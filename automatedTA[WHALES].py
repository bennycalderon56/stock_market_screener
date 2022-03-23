from pandas._config import config
from requests.api import request
from bs4 import BeautifulSoup as Soup
import pandas as pd
import json,csv,os,itertools
import requests
from datetime import date
import lxml
from collections import Counter
import gzip
from requests import get
from urllib.request import urlopen
from iexfinance.stocks import Stock
#############################################################################
#############################################################################
#############################################################################


#############################################################################
#############################################################################
######################scraping/gathering data################################
#############################################################################

def get_parsed_whaledata():
    params = {
        "api_key": "t6SHN1tOUWud",
        "format": "json"
    }
    
    r = requests.get('https://www.parsehub.com/api/v2/projects/tQ5FfawFr-wb/last_ready_run/data',params=params)
    
    jdata = json.dumps(r.text, indent = 4)

    serial = jdata.encode('utf-8')

    with open('data.json.gz', 'wb') as f:
        f.write(gzip.compress(serial))
   
    serial, vol, jdata = None, None, None    
    
    with open('data.json.gz', 'rb') as f:
        serial = gzip.decompress(f.read())
    
    jdata = serial.decode('utf-8')

    vol = json.loads(jdata)
    # retreiving option data from volume json
    options = json.loads(vol)
    opt = options.get('option')

    return opt
    


def get_gains():
    Movergain = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/stock/gainers?apikey=2a4bf570d78de5dea1ca8e7e1e6244c0")
    #GAINS 
    tickerGain = json_extract(Movergain,'ticker')
    # tGainPer = json_extract(Movergain,'changesPercentage')
    # gains = dict(zip(tickerGain,tGainPer))
    # #print(gains)
    return tickerGain

def get_loss():
    Moverloss = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/stock/losers?apikey=2a4bf570d78de5dea1ca8e7e1e6244c0")
    #LOSSES
    tickerLoss = json_extract(Moverloss,'ticker')
    # tLossPer = json_extract(Moverloss,'changesPercentage')
    # loss = dict(zip(tickerLoss,tLossPer))
    return tickerLoss

def get_active():
    Moveractive = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/stock/actives?apikey=2a4bf570d78de5dea1ca8e7e1e6244c0")
    #ACTIVE
    tickerActive = json_extract(Moveractive,'ticker')
    # tActive = json_extract(Moveractive,'changes')
    # active = dict(zip(tickerActive,tActive))
    return tickerActive



def get_jsonparsed_data(url):
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

def json_extract(obj,key):
    arr = []
    def extract(obj,arr,key):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if isinstance(v,(dict,list)):
                    extract(v,arr,key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj,list):
            for item in obj:
                extract(item,arr,key)
        return arr
    values = extract(obj,arr,key)
    return values


#############################################################################
#############################################################################
######################COMPILING DATA TOGETHER################################
#############################################################################


def unusual_csv():
    unusual_opt = get_parsed_whaledata()
    # print(unusual_opt)
    with open('whales.csv','w') as csvfile:
        fieldnames = ['name','ask','exp','vol','oi','sec','mip','url']
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unusual_opt)
        print("completed unusual csv")


def gather_active():
    #MERGE ALL TICKERS WANTED IN ORDER FEED INTO TAs CURL

    unusual_csv()
    Dgains = get_gains()
    Dloss = get_loss()
    Dactive = get_active()

    #AS OF NOW WE DONT NEED CSV
    myFile = open('activeData.csv', 'w')
    with myFile:
        writer = csv.writer(myFile)

        writer.writerow(Dgains)
        writer.writerow(Dloss)
        writer.writerow(Dactive)
    print("gathered all data into active csv")
    #TURN ALL THAT CSV INFO INTO A DICT
    tickers=[]
    file = open(os.path.join('activeData.csv'))
    reader = csv.reader(file, delimiter=',')
    for row in reader:
        for column in row:
            tickers.append(column)
    
    #IF WANTING TO SEARCH ONLY 1 TICKER DO IT HERE
    tick =['NNDM','GEVO']
    return tick
    #NEED TO FIX WHALES DICTIONARY, TICKER ONLY, IT PRINTS STRIKE WITH IT
    # with open('whales.csv','r') as infile:
    #     reader = csv.reader(infile)
    #     with open('whales_new.csv','w') as outfile:
    #         writer = csv.writer(outfile)
    #         VOLnames = {rows[0] for rows in reader}       


#############################################################################
#############################################################################
######################TECHNICAL INDICATORS###################################
#############################################################################



def get_ema21():
    #read in csv data from gather_active & unusual whale
    tickers = gather_active()
    #tickers=['NNDM','GEVO']
    result = {}
    todaysEMA = []
  
    #GRAB ONLY THE 1st ITEM EVERY TIME; AS IT IS TODAYS EMA.
    for i in tickers:
        #print(i)
        confidence = 0
        try:
            ema = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/technical_indicator/daily/{}?period=21&type=ema&apikey=2a4bf570d78de5dea1ca8e7e1e6244c0".format(i))
            todaysEMA = ema[0]#since 0 is the latest entry(being today) in the ema dict
            ema21 = json_extract(todaysEMA,'ema')
            vol = json_extract(todaysEMA,'volume')
            close = json_extract(todaysEMA,'close')
            #do calculations here ex[if close > ema50 confidence+1]
            #since close is greater than the ema50 this means that it has a solid 50day support.
            if close > ema21:
                confidence = confidence + 1
            result[i] = confidence
        except:
            print("{} ema21 failed to execute".format(i))
    
    return result



def get_sma200():    
    tickers = gather_active()
    result = {}
    todaysSMA = []
  
    #GRAB ONLY THE 1st ITEM EVERY TIME; AS IT IS TODAYS EMA.
    for i in tickers:
        #print(i)
        confidence = 0
        try:
            sma = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/technical_indicator/daily/{}?period=200&type=sma&apikey=2a4bf570d78de5dea1ca8e7e1e6244c0".format(i))
            todaysSMA = sma[0]#since 0 is the latest entry(being today) in the ema dict
            sma200 = json_extract(todaysSMA,'sma')
            vol = json_extract(todaysSMA,'volume')
            close = json_extract(todaysSMA,'close')
            #do calculations here ex[if close > ema50 confidence+1]
            #since close is greater than the ema50 this means that it has a solid 50day support.
            if close > sma200:
                confidence = confidence + 1
            result[i] = confidence
        except:
            print("{} sma200 failed to execute".format(i))
    
    return result


def get_tma30():    
    tickers = gather_active()
    result = {}
    todaysTMA = []
  
    #GRAB ONLY THE 1st ITEM EVERY TIME; AS IT IS TODAYS EMA.
    for i in tickers:
        #print(i)
        confidence = 0
        try:
            tma = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/technical_indicator/daily/{}?period=30&type=tema&apikey=2a4bf570d78de5dea1ca8e7e1e6244c0".format(i))
            todaysTMA = tma[0]#since 0 is the latest entry(being today) in the ema dict
            tma30 = json_extract(todaysTMA,'sma')
            #vol = json_extract(todaysTMA,'volume')
            close = json_extract(todaysTMA,'close')
            #do calculations here ex[if close > ema50 confidence+1]
            #since close is greater than the ema50 this means that it has a solid 50day support.
            if close > tma30:
                confidence = confidence + 1
            result[i] = confidence
        except:
            print("{} tma30 failed to execute".format(i))
    
    return result


def get_rsi():    
    tickers = gather_active()
    result = {}
    todaysRSI = []
  
    #GRAB ONLY THE 1st ITEM EVERY TIME; AS IT IS TODAYS EMA.
    for i in tickers:
        #print(i)
        confidence = 0
        try:
            rsi = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/technical_indicator/daily/{}?&type=rsi&apikey=2a4bf570d78de5dea1ca8e7e1e6244c0".format(i))
            todaysRSI = rsi[0]#since 0 is the latest entry(being today) in the ema dict
            rsi7 = json_extract(todaysRSI,'sma')
            #vol = json_extract(todaysRSI,'volume')
            #close = json_extract(todaysRSI,'close')
            
            #as of now im doing less than 60 on the 7 day rsi period
            if rsi7 < 60:
                confidence = confidence + 1
            result[i] = confidence
        except:
            print("{} rsi7 failed to execute".format(i))
    
    return result


def get_adx():    
    tickers = gather_active()
    result = {}
    todaysADX = []
  
    #GRAB ONLY THE 1st ITEM EVERY TIME; AS IT IS TODAYS EMA.
    for i in tickers:
        #print(i)
        confidence = 0
        try:
            adx = get_jsonparsed_data("https://financialmodelingprep.com/api/v3/technical_indicator/daily/{}?&type=adx&apikey=2a4bf570d78de5dea1ca8e7e1e6244c0".format(i))
            todaysADX = adx[0]#since 0 is the latest entry(being today) in the ema dict
            adx14 = json_extract(todaysADX,'sma')
            #vol = json_extract(todaysADX,'volume')
            close = json_extract(todaysADX,'close')
            #do calculations here ex[if close > ema50 confidence+1]
            #since close is greater than the ema50 this means that it has a solid 50day support.
            if adx14 > 25:
                confidence = confidence + 1
            result[i] = confidence
        except:
            print("{} adx14 failed to execute".format(i))
    
    return result



def all_TAs():
    #THIS WILL CALL ALL TA FUNCTIONS
    ema21C = get_ema21()
    sma200C = get_sma200()
    tma30C = get_tma30()
    rsi7C = get_rsi()
    adx14C = get_adx()
    res = Counter(ema21C) + Counter(sma200C) + Counter(tma30C) +Counter(rsi7C) + Counter(adx14C)
    test = sorted(res.items(),reverse=True,key=lambda x: x[1])
    print(test)
    print(res)
    



# def final_product():
#     #here is where it would compile it all in one csv
#     with open('automatedTA.csv','w') as csvfile:
#         fieldnames = ['','','','','','']
#         writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
    

def main():
    all_TAs()
    


if __name__ == "__main__":
    main()

