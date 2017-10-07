# -*- coding: utf-8 -*-
# Скрипт для подгрузки данных котировок

from datetime import datetime as dt
from providers import finam
import time, os

def trier(times, func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except IOError as e:
        if times:
            # one more time!
            print("Failed, will try again!")
            trier(times-1, func, *args, **kwargs)
        else:
            # give up!
            raise e

def import_data(FROM, TO, FREQ, DIR, N_TRIES):
    print("Старт загрузчика рыночных данных")
    tickers = open('data/tickers.txt').readlines()
    if not os.path.isdir(DIR):
        print("Директория %s не найдена, создаю" % DIR)
        os.makedirs(DIR)
    for sym in tickers:
        sym = sym.strip() # no newline
        if os.path.exists(DIR + os.sep + '%s.pickle' % sym):
            print("%s уже загружен, пропускаю" % sym)
            continue
        print("Загрузка %s" % sym)
        fin_data = trier(N_TRIES, finam.get_quotes, sym, FROM, TO, FREQ)
        if not fin_data is None and len(fin_data):
            print("Сохранение CSV")
            fin_data.to_csv(DIR + os.sep + '%s.csv' % sym)
            print("Сохранение бинарника")
            fin_data.to_pickle(DIR + os.sep + '%s.pickle' % sym)
        else:
            print("Проблема с %s, пропускаю!" % sym)
