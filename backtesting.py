# -*- coding: utf-8 -*-
# Скрипт для запуска бэктеста нашей стратегии

import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
sns.set(style="darkgrid",  palette="muted", rc={'figure.figsize':(16,5)})

import pandas as pd
import sys, pickle, logging

log = logging.getLogger('run_backtest')

from intraday.pair_backtest import PairTrader, PairReporter
import private_strategies as s
from datetime import time

# Baktester settings
from settings import *

# Enable Logging
logging.basicConfig()
log.setLevel(logging.INFO)
logging.getLogger('pair_trading.strategy').setLevel(logging.INFO)

log.info("Backtester started with settings:")
log.info("\tInit cap: %d" % initial_capital)
log.info("\tCommission: %f" % commission)
log.info("\tLot sizes: %s" % str(lots))
log.info("\tSpread sizes: %s" % str(spreads))
log.info("\tStrategy params (δ,λ,zₑₙₜ,zₑₓ): %.2e, %.2e, %.2f, %.2f" % 
    (delta,lyambda,zscore_enter,zscore_exit))

if len(sys.argv) <> 3:
    # Explain usage
    log.error("Not enough arguments")
    print("Expected cmdline: backtest_pair.py SYMBOL1 SYMBOL2")
    sys.exit(-1)
sym1, sym2 = sys.argv[1:]

try:
    log.info("Loading data from pickle")
    data1 = pickle.load(open('data/%s-%s.pickle' % (sym1, data_freq)))
    data2 = pickle.load(open('data/%s-%s.pickle' % (sym2, data_freq)))
except IOError:
    log.error("Can't read data! Exiting")
    sys.exit(-1)
log.info("Constructing dual panel for %s and %s..." % (sym1, sym2))
data1 = data1.drop(data1.index.get_duplicates())
data2 = data2.drop(data2.index.get_duplicates())
pairs = pd.Panel({sym1:data1, sym2:data2},
    major_axis = data1.index.intersection(data2.index))

# Period for backtest
test_data = pairs.ix[:,test_period[0]:test_period[1]]
index = test_data.major_axis

# Init trader & reporter
trader = PairTrader(initial_capital, (sym1, sym2),
    lots = lots, spreads=spreads)
trader.commission = commission
trader.fixed_commission = fixed_commission
reporter = PairReporter( (sym1,sym2), r_free=r_free_rate, 
    num_workdays=num_workdays)

# Init strategy
strategy = s.PHKBollinger((sym1, sym2),
    zscore_enter=zscore_enter, zscore_exit=zscore_exit, 
    delta=delta, lyambda=lyambda)

log.info("Backtesting...")
log.info("Start balance [%s] is %.0f" % (index[0], initial_capital))
portfolio = trader.backtest(strategy, test_data)
log.info("End balance [%s] is %.0f" % (index[-1], portfolio.ix[-1,'EQ']))

log.info("Reporting results")
reporter.report(portfolio, plot_EQ=False, plot_positions=False)
# strategy._plot_dbg()
