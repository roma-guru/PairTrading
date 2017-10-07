# -*- coding: utf-8 -*-
# Простая реализация фильтра Калмана
import numpy

class KalmanFilter:
    def __init__(self,A, x, P, Q, R):
        self.A = A                      # State transition matrix.
        self.current_state_estimate = x # Initial state estimate.
        self.current_prob_estimate = P  # Initial covariance estimate.
        self.Q = Q                      # Estimated error in process.     
        self.R = R                      # Estimated error in measurements.   

    def step(self, measurement_vector, measurement_matrix):
        self.H = measurement_matrix
        #---------------------------Prediction step-----------------------------    
        predicted_state_estimate = self.A * self.current_state_estimate
        predicted_prob_estimate = (self.A * self.current_prob_estimate) * numpy.transpose(self.A) + self.Q
        #--------------------------Observation step-----------------------------     
        innovation = measurement_vector - self.H*predicted_state_estimate
        innovation_covariance = self.H*predicted_prob_estimate*numpy.transpose(self.H) + self.R
        #-----------------------------Update step-------------------------------
        kalman_gain = predicted_prob_estimate * numpy.transpose(self.H) * numpy.linalg.inv(innovation_covariance)
        self.current_state_estimate = predicted_state_estimate + kalman_gain * innovation
        # We need the size of the matrix so we can make an identity matrix.    
        size = self.current_prob_estimate.shape[0]     # eye(n) = nxn identity matrix.     
        self.current_prob_estimate = (numpy.eye(size)-kalman_gain*self.H)*predicted_prob_estimate
