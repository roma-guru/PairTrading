# -*- coding: utf-8 -*-
# Главный файл со стратегией!!

import logging
import math
from array import array
from intraday.strategies.base import Base

import numpy as np
from statsmodels.tsa.filters.hp_filter import hpfilter
from kalman import KalmanFilter

log = logging.getLogger('pair_trading.strategy')

class PHKBollinger(Base):
    """
    Prescott-Hodrick Kalman Bollinger mean-reverting.
    Advanced pair-trading:
    1) Use Kalman filter to hedge stock pair and get intercept/spread
    2) Use Hodrick-Prescott filter to get trend/oscilation from spread
    3) Use Bollinger bands for it's local mean-reversion
    """
    def __init__(self, tickers, zscore_enter, zscore_exit, lyambda, delta, window=1000):
        """
        Constructor.
        Params:
            tickers - pair tuple of 2 tickers
            zscore_enter - entry level of mean deviation
            zscore_exit - exit level of mean deviation (0 means mean-reversion)
            lyambda - Hodrick-Prescott λ parameter
            delta - Kalman observation variance param δ
            window - number of points at the beginning used to Kalman calibration
                1000 by default
        """
        log.debug(self.__class__.__name__+" init")
        self.delta = delta
        self.lyambda = lyambda
        self.sym1, self.sym2 = tickers
        self.zscore_exit = zscore_exit
        self.zscore_enter = zscore_enter
        
        self.window = window
        # Debug data saved for the later
        self._dbg_data = dict(delta=array('f'),
            beta=array('f'), intercept=array('f'), 
            zscore=array('f'), vol=array('f'),
            trend=array('f'))
        # Current position
        self.curr_pos = {self.sym1:0., self.sym2:0.}
        # Take profit stop
        self.take_prft = None

        # Kalman filter object
        self.kfilter = KalmanFilter(A=np.eye(2), 
            Q=delta*np.eye(2), 
            R=np.matrix(1),
            x=np.zeros( 2 ), 
            P=np.ones((2, 2)) )

    # Utility function to determine current state
    def _position(self):
        return not self.curr_pos is None and self.curr_pos[self.sym1]

    def handle_moment(self, prev_data):
        now = prev_data.major_axis[-1]
        x = prev_data.ix[self.sym1, :, 'close']
        y = prev_data.ix[self.sym2, :, 'close']
        
        # Step 1: Kalman observation
        self.kfilter.step(
            measurement_vector=np.matrix(y[now]), 
            measurement_matrix=np.matrix([x[now],1]))
        if len(x) < self.window:
            return (self.curr_pos, "Not enough points")

        # Window for Prescott-Hodrick
        y_window = y[-self.window:]
        x_window = x[-self.window:]
        beta = self.kfilter.current_state_estimate[0,0]
        intercept = self.kfilter.current_state_estimate[1,0]
        # Residuals after dynamic regression
        deltas = y_window - beta * x_window - intercept
        # Last one
        delta = deltas[-1]
        # Debug data
        self._dbg_data['delta'].append(delta)
        self._dbg_data['beta'].append(beta)
        self._dbg_data['intercept'].append(intercept)

        # Step 2: Here goes Prescott-Hodrick
        osc, trend = hpfilter(deltas.values, self.lyambda)
        vol = np.std(osc)
        zscore = osc[-1]/vol
        # Debug data
        self._dbg_data['zscore'].append(zscore)
        self._dbg_data['vol'].append(vol)
        self._dbg_data['trend'].append(trend[-1])

        # Step 3: Bollinger Bands
        # Higher bound
        pos = np.sign(self._position())
        if zscore > self.zscore_enter and not pos:
            log.info("Entering long ratio @ " + str(now))
            log.debug("Zscore: %.2f (%.4f/%.4f)" % (zscore,osc[-1],vol))
            self.curr_pos = {self.sym2: -1/(1.+beta), self.sym1:beta/(1.+beta)}
            return (self.curr_pos, "X below mean")
        # Lower bound
        elif zscore < -self.zscore_enter and not pos:
            log.info("Entering short ratio @ " + str(now))
            log.debug("Zscore: %.2f (%.4f/%.4f)" % (zscore,osc[-1],vol))
            self.curr_pos = {self.sym2: 1/(1.+beta), self.sym1:-beta/(1.+beta)}
            return (self.curr_pos, "X above mean")
        # Middle band
        elif pos and pos*zscore < pos*self.zscore_exit:
            # if self.take_prft is None or sign*delta > sign*self.take_prft:
            #     self.take_prft = delta
            #     log.debug("New Take-Profit: %.2f" % self.take_prft)
            # else:
            log.info("Exiting @ " + str(now))
            log.debug("Zscore: %.2f (%.4f/%.4f)" % (zscore,osc[-1],vol))
            self.curr_pos = {self.sym1:0., self.sym2:0.}
            self.take_prft = None
            return (self.curr_pos, "Mean reverted")

        return (self.curr_pos, None)

    def _plot_dbg(self):
        import matplotlib.pyplot as plt
        strategy = self
        data = strategy._dbg_data
        fig, axes = plt.subplots(2,2, sharex=True)
        axes[0,0].plot(data['beta'], label = 'Betas')
        axes[0,1].plot(data['intercept'], label = 'Intercepts')
        axes[1,0].plot(data['delta'], label = 'Deltas')
        # axes[1,0].plot(data['trend'], 'g-', label = 'Trend')
        axes[1,1].plot(data['zscore'], label = 'Z-scores')
        n = len(data['zscore'])
        axes[1,1].plot(np.ones(n)*strategy.zscore_enter, 'r--')
        axes[1,1].plot(np.ones(n)*strategy.zscore_exit, 'r:')
        axes[1,1].plot(-np.ones(n)*strategy.zscore_enter, 'r--')
        axes[1,1].plot(-np.ones(n)*strategy.zscore_exit, 'r:')
        axes[1,1].plot(data['vol'], 'k-', label = 'Volatilily')
        for x in axes.flat: x.legend()
        if plt.get_backend()=='TkAgg':
            plt.get_current_fig_manager().window.wm_geometry("1000x600+900+50")
        plt.show()
