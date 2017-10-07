# -*- coding: utf-8 -*-
# Настройки бектестера

initial_capital = 100000
commission = .0003
fixed_commission = 0
spreads = (.05, .05)
lots = (10, 10)

# Безрисковая ставка: ГКО-ОФЗ 10% годовых
r_free_rate = .1

# Рабочих дней на бирже
num_workdays = 247

# Потоков для оптимизации
num_workers = 6

data_freq = '5m'
opt_period = ('1-2014','6-2014')

# test_period = ('1-2014','6-2014')
test_period = ('7-2014','11-2014')
# test_period = ('1-2015','5-2015')

# Параметры стратегии
delta = 1e-15
lyambda = 1e15
zscore_enter = .7
zscore_exit = -.1
