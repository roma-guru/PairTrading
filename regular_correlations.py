# -*- coding: utf-8 -*-
# Скрипт для нахождения наиболее скореллированных инструментов

from datetime import timedelta as delta, datetime as dt
import pandas as pd
import numpy as np

print "Loading data"
tickers = open('data/tickers.txt').read().split('\n')
t_map= {}
for t in tickers:
    df = pd.read_pickle('data/%s-5m.pickle'%t)
    t_map[t] = df.groupby(df.index).first()
# Panel from dict of frames
bars = pd.Panel(data=t_map)

print "Calculating correlations"
start = dt(2014,1,1)
t_map = {}
n = 0
while start < bars.major_axis[-1]:
    end = start + delta(weeks=4)
    corr_mat = pd.DataFrame(index=tickers, columns=tickers)
    for i in range(len(tickers)):
        t1 = tickers[i]
        corr_mat.ix[t1,t1] = 1.0
        for j in range(i+1, len(tickers)):
            t2 = tickers[j]
            t = corr_mat.ix[t1,t2] = corr_mat.ix[t2,t1] = bars[t1].ix[start:end,'close'].corr(bars[t2].ix[start:end,'close'])
            if t==np.nan:
                print "Kakaya-to Xyuta c ", t1,t2
    t_map[n] = corr_mat
    start = end
    n+=1

print "Calculating scores"
corr_panel = pd.Panel(data = t_map)
scores = {}
for i in range(len(tickers)):
    for j in range(i+1, len(tickers)):
        score = 0
        for p in range(n):
            c = corr_panel[p].iloc[i,j]
            if c>0.7:
                score += p*c
        scores["%s-%s" % (tickers[i],tickers[j])] = score

print "And the winners are:"
winners = sorted(filter(lambda x:x[1]>.2*(1+n)*n, scores.items()), 
    key=lambda x:x[1], reverse=True)
for p in winners:
    print p
