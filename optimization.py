# -*- coding: utf-8 -*-
# Скрипт для запуска процесса оптимизации

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import sys, pickle, logging, curses, time
from math import sqrt
from multiprocessing import Pool, cpu_count

from datetime import datetime as dt
log = logging.getLogger('pair_trading.optimizer')
log.addHandler(logging.FileHandler('logs/Optimization_%s.log' % str(dt.now().isoformat())))
log.setLevel(logging.INFO)

from intraday.pair_backtest import PairTrader, Utils
import private_strategies as s

# Optimization settings
from settings import *
r_free_daily = r_free_rate * initial_capital  / num_workdays

def f1(params,test_data):
    delta, lyambda, zscore_enter, zscore_exit = params
    strategy = s.PHKBollinger((sym1, sym2),
                    lyambda=lyambda, delta=delta,
                    zscore_enter=zscore_enter, zscore_exit=zscore_exit)
    trader.initial_capital = initial_capital
    portfolio = trader.backtest(strategy, test_data)
    EQ = portfolio['EQ']
    long_trades = portfolio['long_trades']
    short_trades = portfolio['short_trades']
    long_returns = Utils.get_trade_returns(long_trades, EQ)
    short_returns = Utils.get_trade_returns(short_trades, EQ)
    total_returns = long_returns + short_returns
    daily_returns = total_returns.resample('B', how='sum').fillna(0)
    sharpe = Utils.annual_sharpe(daily_returns, r_free_daily, num_workdays)
    drawdown, duration = Utils.max_drawdown(EQ)
    return total_returns.sum(), sharpe, drawdown

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger('pair_trading.strategy').setLevel(logging.ERROR)
    logging.getLogger('intraday.backtest').setLevel(logging.ERROR)

    log.info("Optimization started with settings:")
    log.info("\tInit cap: %d" % initial_capital)
    log.info("\tCommission: %f" % commission)
    log.info("\tLot sizes: %s" % str(lots))
    log.info("\tSpread sizes: %s" % str(spreads))
    log.info("\tNumber of processes: %d" % num_workers)

    if len(sys.argv) <> 3:
        log.error("Not enough arguments")
        log.error("Expected cmdline: backtest_pair.py SYMBOL1 SYMBOL2")
        sys.exit(-1)
    sym1, sym2 = sys.argv[1:]

    try:
        log.info("Loading data from pickle")
        data1 = pickle.load(open('data/%s-%s.pickle' % (sym1, data_freq)))
        data2 = pickle.load(open('data/%s-%s.pickle' % (sym2, data_freq)))
    except IOError as e:
        log.error(e)
        sys.exit(-1)
    
    log.info("Constructing dual panel for %s and %s" % (sym1, sym2))
    data1 = data1.drop(data1.index.get_duplicates())
    data2 = data2.drop(data2.index.get_duplicates())
    pairs = pd.Panel({sym1:data1, sym2:data2}, 
        major_axis = data1.index.intersection(data2.index))
    # pairs = pairs.dropna()

    trader = PairTrader(initial_capital, (sym1,sym2), lots=lots, spreads=spreads)
    trader.commission = commission
    test_data = pairs.ix[:,opt_period[0]:opt_period[1]]

    futs = {}
    pool = Pool(processes = num_workers)
    
    log.info("Optimization start")
    # for freq in ['1min','3min','5min','7min','10min','15min','20min','30min']:
    #     test_data = pd.Panel(dict(map(lambda item:(item,
    #         all_data[item].asfreq(freq).dropna()), all_data.items)))
    for delta in [1e-8,1e-10,1e-13,1e-15,1e-17]:
        for lyambda in [1e8,1e10,1e13,1e15,1e17]:
    # for zscore_enter in np.linspace(0.5,2,7):
        # for zscore_exit in np.linspace(-zscore_enter,zscore_enter,7):
            params = (delta, lyambda, zscore_enter, zscore_exit)
            futs[params] = pool.apply_async(f1,
                args=(params,test_data))

    max_sharpe = 0
    best_drawdown = np.inf
    best_params = None
    best_profit = 0
    all_tasks = len(futs)
    done_tasks = 0
    try:
        while done_tasks<all_tasks:
            time.sleep(1)
            for params in futs.keys():
                result = futs[params]
                if result.ready():
                    (profit, sharpe, drawdown) = result.get()
                    del futs[params]
                    done_tasks += 1
                    log.info("For params %.2e %.2e %f %f:" % params)
                    log.info("\tProfit=%+.2f, Sharpe=%.2f, Drawdown=%.2f" % (profit, sharpe, drawdown))
                    if sharpe > max_sharpe:
                        best_params = params
                        best_drawdown = drawdown
                        best_profit = profit
                        max_sharpe = sharpe
    except KeyboardInterrupt:
        log.warn("Terminated!")
    finally:
        pool.terminate()
    
    log.info("Optimization end")
    log.info("Best params are %s" % str(best_params))
    log.info("Sharpe is %.2f" % max_sharpe)
    log.info("Profit is %+.2f" % best_profit)
    log.info("Drawdown is %.2f" % best_drawdown)

    # This is for rerunning in the same shell (stop old logs)
    log.handlers.pop()
