# Utilities

import numpy as np
import scipy.signal as signal
from scipy.optimize import curve_fit
import traceback

class SignalProc:
	'''
	utility functions for signal processing in slice physiology data
	'''
	def __init__(self):
		pass

	def thmedfilt(self, x, wsize, thresh):
		'''
		Median filter with threshold, only sample points with value larger 
		than a threshold are filtered.

		Paramters
		---------
		x: array_like
			Input signal
		wsize: int
			Median filter window size
		thresh: float
			Threshold for filter

		Returns
		-------
		z: array
			Filterd signal
		'''

		y = signal.medfilt(x, wsize)
		z = np.where(thresh < abs(y - x), y, x)
		return z

	def smooth(self, x, sr, band, ftype, btype):
		'''
		Lowpass filter the signal with Butterworth filter to smooth it

		Paramters
		---------
		x: array_like
			Signal trace.
		sr: float
			Sampling rate.
		band: float or list
			Critical freqency for lowpass filter.
		ftype: string, optional
			Type of filters. "butter", "bessel".
		btype: string, optional
			Bind type. "bandpass", "lowpass", "highpass"

		Returns
		-------
			y: array_like
				Smoothed trace.
		'''

		if btype == "lowpass" or btype == "highpass":
			b, a = signal.iirfilter(4, band / sr * 2, btype = btype,
					ftype = ftype)
		else:
			b, a = signal.iirfilter(4, [b / sr * 2 for b in band], 
					btype = btype, ftype = ftype)
		y = signal.filtfilt(b, a, x)
		return y

	def decayFit(self, x, sr, scale, ft1, ft2, sign = 1, p0 = None):
		'''
		Fit exponential decay, used mostly in seal test analysis.

		Parameters
		----------
		x: numpy.array
			Sample trace to fit.
		sr: float
			Sampling rate.
		scale: float
			Scaling ratio of amplitude of the trace for better fitting.
		ft1: int
			Index of start of curve fitting.
		ft2: int
			Index of end of curve fitting.
		sign: int, optional
			-1 or 1, sign relative to baseline. Default is 1.
		p0: array_like, optional
			Initial guess of fit function parameters, default as None, in
			which case a guess will be made by this function.

		Returns
		-------
		x0: float
			Initial amplitude.
		xs: float
			Steady state amplitude.
		tau: float
			Decay time constant.
		'''
		fit_time = np.arange(ft2 - ft1)  # time array of exponential fit
		fit_x = np.array(x[ft1:ft2]) * scale  # trace within the fit time period
		if p0 == None:
			x2 = fit_x[-1]
			g_x0 = fit_x[0]  # initial guess of x0
			g_tau_ind = np.argwhere(sign * (fit_x - x2) < \
				sign * (g_x0 - x2) / np.e)
			g_tau = g_tau_ind[0][0]  # initial guess of tau
			p_0 = [g_x0, g_tau, x2]  # initial guess
		else:
			p_0 = p0
		'''
		bnd = ([-np.inf, 0, 0], \
				[np.inf, t2 - t1, np.inf])  # bounds
		'''
		try:
			popt, pcov = curve_fit(self.fit_fun, fit_time, fit_x, p0 = p_0)
			fit_x0, tau, fit_xs = popt
			# x0 = self.fit_fun((t0 - t1), fit_x0, tau, fit_xs) / scale
			x0 = fit_x0 / scale
			xs = fit_xs / scale
			tau = tau / sr
			return x0, xs, tau
		except TypeError as e:
			print("Fitting Error")
			print(traceback.format_exc())
			raise
	
	def fit_fun(self, t, x0, tau, xs):
		'''
		Exponential decay function.

		Parameters
		----------
		t: float
			Time, independent variable.
		x0: float
			Initial amplitude.
		xs: float
			Steady state amplitude.
		tau: float
			Decay time constant.

		Returns
		-------
		xt: float
			Amplitude at time t.
		'''
		xt = xs + (x0 - xs) * np.exp(-t / tau)
		return xt
