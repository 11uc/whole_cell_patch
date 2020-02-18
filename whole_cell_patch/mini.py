# Detect spontaneous mini postsynaptic responses and 
# calculate their properties.

import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from .project import Project
from .analysis import Analysis
from .process import SignalProc
from . import plot

class Mini(SignalProc, Analysis):
	'''
	Analyze mini postsynaptic response properties, including 
	decay time constant, amplitude and frequency.
	'''

	def __init__(self, inTxtWidget, projMan = None):
		'''
		Load spike detection parameters from the grand parameter file
		and raw data information.

		Parameters
		----------
		projMan: Project
			Object containing information about the project including 
			raw data and some parameters.
		'''
		self.projMan = projMan
		# default mini analysis parameters
		self.setBasic(self.loadDefault("basic"))
		SignalProc.__init__(self)
		Analysis.__init__(self, inTxtWidget)

	def loadDefault(self, name):
		'''
		Override parent class method.
		'''
		default = {
				"basic": {"sign" : -1, 
					"medianFilterWinSize" : 5, 
					"medianFilterThresh" : 30e-12, 
					"lowBandWidth" : 300, 
					"riseSlope" : 4.5e-9, 
					"riseTime" : 5e-3, 
					"baseLineWin" : 10e-3, 
					"minAmp" : 1e-11, 
					"minTau" : 1.2e-3, 
					"residual" : 0.2, 
					"onTauIni" : 1, 
					"offTauIni" : 20, 
					"stackWin" : 7e-3, 
					"scale" : 1e12},
				"batchMini": {"protocol": '',
					"win": [0, 0],
					"verbose": 0},
				"aveMini": {"protocol": '',
					"cells": [],
					"RinTh": 0,
					"numTh": 0}}
		return default[name]
	
	def setBasic(self, param):
		'''
		Set basic analysis parameters since it's not passed in any function.

		Parameters
		----------
		param: dictionary
			Basic parameters.
		'''
		self.miniParam = param
		self.miniParam["riseSlope"] *= param["scale"]
		self.miniParam["minAmp"] *= param["scale"]

	def miniAnalysis(self, trace, sr, win = [0, 0], verbose = 0):
		'''
		Detect minis and analyze them
		Criterions:
		  1. Rise time short enough
		  2. Amplitude large enough
		  3. Decay fit exponential curve with low enough residual
		  4. Decay time constant big enough

		Parameters
		----------
		trace: numpy.array
			Recorded electric signal trace.
		sr: float
			Sampling rate.
		win: array_like, optional
			With 2 scalars, time window in which the minis are analyzed. Default is
			[0, 0], takes the entire trace.
		verbose: int, optional
			Whether to display intermediate results for inspection.
			1 - Plot detected minis.
			2 - Plot fitting of each mini.

		Returns
		-------
		miniProps: pandas.DataFrame
			Mini properties, row are action potentials 
			in the trial and columns are properties
		'''
		# mini properties
		miniRises = []  # valid minis' rise time points
		miniPeaks = []  # valid minis' peak time points
		miniAmps = []	# valid mini's peak amplitudes
		miniDecayTaus = []  # valid mini's decay time constants
		print(win)
		if win[0] != win[1]:
			x = trace[int(sr * win[0]):int(sr * win[1])] * \
					self.miniParam['sign']
		else:
			x = trace * self.miniParam['sign']
		# rig defect related single point noise
		x = self.thmedfilt(x, self.miniParam['medianFilterWinSize'], \
				self.miniParam['medianFilterThresh'])
		# scale
		x = x * self.miniParam["scale"]
		print(len(x))
		# remove linear shifting baseline
		p = np.polyfit(np.arange(len(x)), x, 1)
		x = (x - np.polyval(p, np.arange(len(x))))
		# low pass filter
		fx = self.smooth(x, sr, self.miniParam['lowBandWidth'])
		dfx = np.diff(fx) * sr
		peaks = (0 < dfx[0:-1]) & (dfx[1:] < 0)
		troughs = (dfx[0:-1] < 0) & (0 < dfx[1:])
		# points with local maximum slope, which is also larger than threshold
		rises = (dfx[0:-1] < self.miniParam["riseSlope"]) & \
				(self.miniParam["riseSlope"] < dfx[1:])
		'''
		rises = np.zeros(peaks.shape)
		rises = (dfx[0:-2] < dfx[1:-1]) & (dfx[2:] < dfx[1:-1]) & \
				(self.miniParam['riseSlope'] < dfx[1:-1])
		'''
		# indices of either rises or peaks
		ptrInds = np.concatenate((np.nonzero(peaks | rises | troughs)[0], \
				[int(win[1] * sr)]), axis = None)
		lastRise = -self.miniParam["riseTime"] * sr  # last rise point index
		last2Rise = 0  # the rise point index before last rise point
		baseline = 0  # current baseline level
		peakStack = []	# peaks stacked too close to each other
		for i in range(len(ptrInds) - 1):
			if peaks[ptrInds[i]]:
				if ptrInds[i] - lastRise < self.miniParam['riseTime'] * sr or \
						len(peakStack):
					if (len(peakStack) and ptrInds[i + 1] - peakStack[0] \
								< self.miniParam["stackWin"] * sr):
						peakStack.append(ptrInds[i])
					else:
						if last2Rise < lastRise - \
							int(self.miniParam['baseLineWin'] * sr):
							baseline = np.mean(x[lastRise - \
									int(self.miniParam['baseLineWin'] * sr):\
									lastRise])
						amp = fx[ptrInds[i]] - baseline
						if self.miniParam['minAmp'] < amp or len(peakStack):
							if not len(peakStack) and \
									ptrInds[i + 1] - ptrInds[i] < \
									self.miniParam["stackWin"] * sr and \
									i + 3 < len(ptrInds) and \
									not rises[ptrInds[i + 2]]:
								peakStack.append(ptrInds[i])
							else:
								if len(peakStack):
									amp = np.max(fx[peakStack] - baseline)
									peakStack = []
								sample = x[lastRise:ptrInds[i + 1]]
								# exponential function to fit the decay
								fun = lambda x, t1, t2, a, b, c: \
										a * np.exp(-x / t1) - \
										b * np.exp(-x / t2) + c
								# initial parameter values
								p0 = [self.miniParam["offTauIni"], 
										self.miniParam["onTauIni"],
										fx[lastRise] + amp - baseline, 
										amp, baseline]
								# boundaries
								bounds = ([-np.inf, -np.inf, 0, 0, -np.inf],
										[np.inf, np.inf, np.inf, np.inf, np.inf])
								try:
									popt, pcov = curve_fit(fun, 
											np.arange(len(sample)),
											sample, p0, bounds = bounds,
											loss = "linear", 
											max_nfev = 1e3 * len(sample))
									tau_rise = popt[1] / sr
									tau_decay = popt[0] / sr
									res = np.sqrt(np.sum((
										fun(np.arange(len(sample)), *popt) - \
												sample) ** 2))
									if verbose > 1:
										self.prt("popt: ", popt)
										self.prt("tau rise: ", tau_rise, 
												"tau decay: ", tau_decay, 
												"res: ", res, 
												"time:", lastRise / sr)
										self.prt(self.miniParam["residual"])
										ax = plot.plot_trace(
												x[lastRise:ptrInds[i + 1]], sr,
												fx[lastRise:ptrInds[i + 1]])
										plot.plot_trace(
												fun(np.arange(len(sample)), *popt),
												sr, ax = ax, cl = 'r')
										self.plt(ax)
										self.prt("Continue (c) or step (default)")
										if self.ipt() == 'c':
											verbose = 1
									if self.miniParam['minTau'] < tau_decay \
											and res < self.miniParam['residual']:
										miniPeaks.append(ptrInds[i] / sr)
										miniRises.append(lastRise / sr)
										miniAmps.append(amp / self.miniParam["scale"])
										miniDecayTaus.append(tau_decay)
								except RuntimeError as e:
									self.prt("Fit Error")
									self.prt(e)
								except ValueError as e:
									self.prt("Initialization Error")
									self.prt(e)
			elif rises[ptrInds[i]]:
				last2Rise = lastRise
				lastRise = ptrInds[i]
		miniProps = pd.DataFrame({"peak": miniPeaks, "rise": miniRises,
			"amp": miniAmps, "decay": miniDecayTaus})
		if verbose > 0:
			ax0 = plot.plot_trace(x, sr, fx)
			ax1 = plot.plot_trace(fx, sr, pcl = 'r', 
					points = np.nonzero(rises)[0] / sr)
			plot.plot_trace(fx, sr, pcl = None, ax = ax1,
					points = np.nonzero(peaks)[0] / sr)
			plot.plot_trace(fx, sr, pcl = 'b', ax = ax1,
					points = miniRises)
			ax2 = plot.plot_trace(dfx, sr)
			self.clearPlt()
			self.plt(ax0, 0)
			self.plt(ax1, 1)
			self.plt(ax2, 2)
			self.linkPlt(0, 0, 1, 0)
			self.ipt("Input any thing to continue.")
			self.clearPlt()
		return miniProps

	def batchMiniAnalysis(self, protocol, win = [0, 0], verbose = 1):
		'''
		Analyze minis in all raw data in a certain subfolder/protocol 
		in current data set. Save all the properties in an intermediate 
		hdf5 file in the working directory. In group
		/mini/protocol/[miniProps and trialProps]

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		win: array_like, optional
			With 2 scalars, time window in which the minis are analyzed. Default
			is [0, 0], taking the entire trace.
		verbose: int
			Whether to print progress information.
			0 - No output.
			1 - Print cell and trial numbers.
			2 - Plot detected minis.
			3 - Plot each fitting of a possible mini.
		'''
		# Detect minis and save properties in file
		# trialProps includes window size and total number of minis
		dur = win[1] - win[0]
		miniProps = []
		trialProps = []
		for c, t in self.projMan.iterate(protocol):
			if verbose:
				self.prt("Cell", c, "Trial", t)
			trace, sr, stim = self.projMan.loadWave(c, t)
			props = self.miniAnalysis(trace, sr, win, verbose - 1)
			props.index.name = "id"
			props["cell"] = c
			props["trial"] = t
			props.set_index(["cell", "trial"], append = True, inplace = True)
			miniProps.append(props)
			trialProps.append(pd.DataFrame({"dur": dur, "num": len(props)},
					index = pd.MultiIndex.from_tuples([(c, t)], 
						names = ["cell", "trial"])))
			if self.stopRequested():
				return 0
		miniProps = pd.concat(miniProps, sort = True)
		trialProps = pd.concat(trialProps, sort = True)
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		store.put("/mini/" + protocol + "/miniProps", miniProps)
		store.put("/mini/" + protocol + "/trialProps", trialProps)
		store.close()

	def aveProps(self, protocol, cells = [], RinTh = 0, numTh = 0):
		'''
		Calculate average mini properties. If input resistance is already
		calculate, only use trials with input resistance lower than 
		provided threshold.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.
		RinTh: float, optional
			Maximum input resistance threshold. Used when the input 
			resistances for cells in this protocol/subfolder is calculated.
			By default not applied.
		NumTh: int, optional
			Minimum number of valid trails required to include the
			cell. By default not applied.

		Returns
		-------
		aveMiniProps: pandas.DataFrame
			DataFrame with averge properties for each cell entry.
		'''
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		miniDataF = "/mini/" + protocol + "/miniProps"
		trialDataF = "/mini/" + protocol + "/trialProps"
		miniProps = pd.read_hdf(self.projMan.workDir + os.sep + "interm.h5",
				"/mini/" + protocol + "/miniProps")
		trialProps = pd.read_hdf(self.projMan.workDir + os.sep + "interm.h5",
				"/mini/" + protocol + "/trialProps")
		if miniDataF in store.keys() and trialDataF in store.keys():
			miniProps = store[miniDataF]
			trialProps = store[trialDataF]
			store.close()
			if RinTh > 0 and len(miniProps):
				try:
					stProps = pd.read_hdf(
							self.projMan.workDir + os.sep + "interm.h5",
							"/st/" + protocol + "/stProps")
					analyzedCells = list(set(miniProps["cell"]))
					stProps = stProps.loc[(analyzedCells), :]
					idx = stProps.index[stProps["Rin"] < RinTh]
					miniProps.reset_index("id", inplace = True)
					miniProps.drop("id", axis = 1, inplace = True)
					miniProps = miniProps.loc[idx, :]
					trialProps = trialProps.loc[idx, :]
				except KeyError as e:
					self.prt(e)
					self.prt("Seal test not done for these traces yet,",
							"Rin threshold won't be used.")
			if len(cells):
				cells = list(set(cells) & 
						set(self.projMan.getSelectedCells()) &
						set(miniProps["cell"]))
				miniProps = miniProps.loc[(cells), :]
				trialProps = trialProps.loc[(cells), :]
			aveMiniProps = miniProps.groupby("cell").mean()
			sumTrialProps = trialProps.groupby("cell").sum()
			sumTrialProps["rate"] = sumTrialProps["num"] / sumTrialProps["dur"]
			aveMiniProps = aveMiniProps.merge(sumTrialProps, "left", on = "cell")
			if numTh > 0 and len(miniProps):
				counts = miniProps.groupby("cell").count()
				idx = counts.index[counts.iloc[:, 0] > numTh]
				aveMiniProps = aveMiniProps.loc[idx, :]
			aveMiniProps= aveMiniProps.merge(self.projMan.getAssignedType(), 
					"left", "cell")
			aveMiniProps.to_csv(self.projMan.workDir + os.sep + \
					"mini_" + protocol + ".csv")
			return aveMiniProps
		store.close()

	def profile(self):
		'''
		Override parent class method.
		'''
		basicParam = {"sign" : "int",
				"medianFilterWinSize" : "int", 
				"medianFilterThresh" : "float",
				"lowBandWidth" : "float", 
				"riseSlope" : "float",
				"riseTime" : "float",
				"baseLineWin" : "float",
				"minAmp" : "float",
				"minTau" : "float",
				"residual" : "float",
				"onTauIni" : "float",
				"offTauIni" : "float",
				"stackWin" : "float",
				"scale" : "float"}
		prof = [
			{"name": "Mini Analysis",
				"pname": "batchMini",
				"foo": self.batchMiniAnalysis,
				"param": {"protocol": "protocol",
					"win": "floatr",
					"verbose": "int"}},
			{"name": "Properties", 
				"pname": "aveMini", 
				"foo": self.aveProps,
				"param": {"protocol": "protocol",
					"cells": "intl",
					"RinTh": "float",
					"numTh": "int"}}]
		return basicParam, prof
