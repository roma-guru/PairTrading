import Quandl

def get_quotes(symbol, start, end, freq):
    assert freq=='1d'
    return Quandl.get(symbol, trim_start=start, trim_end=end)