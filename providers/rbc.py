import pandas as pd
from datetime import timedelta, datetime

"""
Undocumented REST API for RBC (rbc.ru)
Parameters:
    ...
"""
BASE_URL = "http://export.rbc.ru/free/micex.0/free.fcgi?period=DAILY\
&tickers=%s&d1=%d&m1=%d&y1=%d&d2=%d&m2=%d&y2=%d&separator=%%2C&data_format=BROWSER"

def get_quotes(symbol, start, end, freq):
    # Only daily data is for free
    assert freq=='1d'
    try:
        return pd.read_csv(BASE_URL % (symbol,
            start.day, start.month, start.year,
            end.day, end.month, end.year),
            sep=',',header=None, names=['ticker','date','open','high','low','close','volume','waprice'],
            date_parser = lambda x:datetime.strptime(x, "%Y-%m-%d"),
            index_col=1).ix[:,1:6]
    except IOError:
        raise IOError("Can\'t read from RBC!")
    except KeyError:
        raise ValueError("Unsupported series frequency!")
    return None