import pandas as pd

"""
Undocumented REST API for Alor (export.alorbroker.ru)
Broken - URL stopped working =(
"""

BASE_URL = "http://export.alorbroker.ru/file.php?board=MICEX&ticker=%s\
&period=%d&from=%s&to=%s&format=5&formatDate=4&formatTime=4\
&fieldSeparator=2&formatSeparatorDischarge=1"

def get_quotes(symbol, start, end, freq):
    freq_codes = {'1m':1, '5m':5, '10m':10, '15m':15, '30m':30, 
                    '1h':60, '1d':1440 }
    date_format = '%d.%m.%Y'
    try:
        url = BASE_URL % (symbol, freq_codes[freq],
            start.strftime(date_format), end.strftime(date_format))
        return pd.read_csv(url, sep=',',header=None, names=['date','time','open','high','low','close','volume'],
            parse_dates={'datetime':[0,1]}, dayfirst=True, infer_datetime_format=True, index_col=0)
    except IOError as e:
        raise e
    except KeyError:
        raise ValueError("Unsupported series frequency!")
    return None