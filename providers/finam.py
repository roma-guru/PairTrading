# -*- coding: utf-8 -*-
import pandas as pd
from datetime import timedelta
from finam_codes import codes
from cgi import escape
import time

"""
Undocumented REST API for Finam (finam.ru)
Parameters:
    market=1 for Stocks
    em - Ticker code (see mapping)
    df - day of beginning
    mf - month of beginning (starts from 0!)
    yf - year of beginning
    dt - day of ending (period is open-ended!)
    mt - month of ending (starts from 0!)
    yt - year of ending
    p - data frequency (0-ticks, 1-min, 2-5min)
    fsp - fill non-liquid periods!
    ...
"""
# Futures: market=14
BASE_URL = "http://export.finam.ru/csv?market=%d&em=%d&code=%s\
&df=%d&mf=%d&yf=%d&dt=%d&mt=%d&yt=%d&p=%d&dtf=4&tmf=4&mstime=on\
&sep=1&sep2=1&datf=5"

freq_codes = {'1m':2, '5m':3, '10m':4, '15m':5, '30m':6, 
                '1h':7, '1d':8, '1w':9, '1M':10}
year = timedelta(weeks=50)
day = timedelta(days = 1)

def get_quotes(symbol, start, end, freq, fill_empty=False, delay=0.1):    
    try:
        requests = []
        while start < end:
            intermed = min(start + year, end)
            export_url = BASE_URL % (codes[symbol][0], codes[symbol][1], escape(symbol), start.day, start.month-1,
                start.year, intermed.day, intermed.month-1, intermed.year, freq_codes[freq])
            if fill_empty: export_url += '&fsp=1'
            requests.append(pd.read_csv(export_url,
                sep=',',header=None, names=['date','time','open','high','low','close','volume'],
                parse_dates={'datetime':[0,1]}, dayfirst=True, infer_datetime_format=True, index_col=0))
            start = intermed + day
            # request delay
            time.sleep(delay)
        return pd.concat(requests)
    except UnicodeDecodeError as e:
        raise IOError("Can\'t read from Finam, check your params!")
    return None