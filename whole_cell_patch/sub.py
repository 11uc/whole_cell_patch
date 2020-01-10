# Analyze subthreshold stimulation in voltage or current clamps
# and calculate related properties including access resistance, 
# input resistance, membrane capacitance, resting potential and sag ratio.

import os
import numpy as np
import pandas as pd
from .project import Project
from .process import SignalProc
from .analysis import Analysis
from . import plot

class Sub(SignalProc, Analysis):
	'''
	Analyze subthreshold responses and calculate properties including
	access resistance, input resistance, membrane capacitance, resting 
	potential and sag ratio.
	'''

	def __init__(self, inTxtWidget, projMan = None):
		'''
		Load time parameters for memebrane capacitor charging fitting 
		and for sag analysis from the grand parameter file and raw data 
		information. All these time are relative to the start point
		of the subthreshold stimulation.

		Parameters
		----------
		inTxtWidget: QLineEdit
			Input line widget of the main window.
		projMan: Project
			Object containing information about the project including 
			raw data and some parameters.
		'''
		self.projMan = projMan
		# default analysis parameters
		self.setBasic(self.loadDefault("basic"))
		SignalProc.__init__(self)
		Analysis.__init__(self, inTxtWidget)
	
	def loadDefault(self, name):
		'''
		Override parent class method.
		'''
		default = {
				"basic": {"baseline_start" : -0.05, 
					"baseline_end": -0.005,
					"steady_state_start": 0.6,
					"steady_state_end": 0.605,
					"fit_start": 0.0002,
					"fit_end": 0.007,
					"scaleV": 1e12,
					"scaleI": 1e3,
					"minTau": 1e-3},
				"batchSub": {"protocol": '',
					"comp": False,
					"clamp": 'v',
					"verbose": 0},
				"aveSub": {"protocol": '',
					"cells": []}}
		return default[name]
	
	def setBasic(self, param):
		'''
		Set basic analysis parameters since it's not passed in any function.

		Parameters
		----------
		param: dictionary
			Basic parameters.
		'''
		self.subParam = param

	def subAnalysis(self, trace, sr, stim, comp = False, clamp = 'v', verbose = 0):
		'''
		Analyze subthreshold responses. 

		Parameters
		----------
		trace: numpy.array
			Recorded electric signal trace.
		sr: float
			Sampling rate.
		stim: array_like
			Stimulation properties of the trace.
		comp: bool, optional
			Whether Rs or Cm compensation has been done, default is not.
		clamp: string, optional
			Voltage (v) or current (i) clamp, default is voltage.
		verbose: int, optional
			Whether to display intermediate results for inspection.

		Returns
		-------
		subProps: pandas.DataFrame
			Sub properties, has one row, columns are properties
		'''
		# sub properties
		baseline = 0  # baseline amplitude
		steadyState = 0  # steady state amplitude
		Rin = 0  # input resistance
		Rs = 0  # access resistance
		Cm = 0  # membrane capacitance
		sag = 0  # sag ratio
		# load parameters
		t_baseline1 =  self.subParam['baseline_start'] + stim[0]
		t_baseline2 = self.subParam['baseline_end'] + stim[0]
		t_steady1 = self.subParam['steady_state_start'] + stim[0]
		t_steady2 = self.subParam['steady_state_end'] + stim[0]
		t_1 = self.subParam['fit_start'] + stim[0]
		t_2 = self.subParam['fit_end'] + stim[0]
		if clamp == 'v':
			scale = self.subParam["scaleV"]  # scale up for better fitting
		else:
			scale = self.subParam["scaleI"]
		minTau = self.subParam["minTau"]  # minimum tau accepted
		# Amplitude parameters
		# Steady state current is the final steady state after sag
		# current stablized.
		steadyState = np.mean(trace[int(t_steady1 * sr):
			int(t_steady2 * sr)])
		# Baseline current before stimulation 
		baseline = np.mean(trace[int(t_baseline1 * sr):
			int(t_baseline2 * sr)])

		mf = None  # medium fitting threshold
		trapped = True
		if comp:
			trapped = False
		while trapped:
			if mf is not None:
				trace = self.thmedfilt(trace, 5, mf)
			try:
				# fit the exponential decay after the voltage step
				# Use the current of the fitted curve at the peak time as I0
				x0, xs, tau = self.decayFit(trace, sr, scale, 
						int(t_1 * sr), int(t_2 * sr), np.sign(stim[2]))
				if verbose or tau < minTau:
					verbose = True
					self.prt('I0 = ', x0)
					self.prt('tau = ', tau)
					self.prt('Is = ', xs)

					pt1 = int(stim[0] * sr)
					# pt2 = int(t_2 * sr)
					pt2 = int(t_steady1 * sr)
					plot_time = np.arange(pt1, pt2) / sr
					if mf is None:
						plot_trace = np.array(trace[pt1:pt2])
					else:
						plot_trace = self.thmedfilt(np.array(trace[pt1:pt2]), 5, mf)
					fit_trace = [self.fit_fun(i, x0, tau, xs) 
							for i in (plot_time - t_1)]
					if tau < minTau:
						ax = plot.plot_trace(plot_trace, sr)
					else:
						ax = plot.plot_trace(plot_trace, sr, fit_trace)
					self.plt(ax)
					ans1 = self.ipt("Apply/Decrease median filter (m),",
							"keep current fitting result (k) or",
							"ignore this result (default).")
					if ans1 == 'm':
						ans2 = self.ipt("Median filter threshold?")
						mf = float(ans2)
					elif ans1 == 'k':
						break
					else:
						trapped = False
				else:
					break
			except TypeError:
				self.prt("Fitting Error.")
				trapped = False
				raise
			except ValueError:  # when input is not a number
				self.prt("Wrong input format.")
		if trapped:  # fit accepted
			if clamp == 'v':
				Rs = stim[2] / (x0 - baseline)
				Rin = stim[2] / (xs - baseline) - Rs
				Cm = tau * (Rin + Rs) / Rin / Rs
				# sag = (xs - steadyState) / (baseline - steadyState)
				sg = np.sign(stim[2])
				m = sg * np.min(sg * trace[int(t_2 * sr):int(t_steady1 * sr)])
				sag = (m - steadyState) / (baseline - steadyState)
			elif clamp == 'i':
				Rs = (x0 - baseline) / stim[2]
				Rin = (xs - baseline) / stim[2] - Rs
				Cm = tau / Rin
				# sag = (xs - steadyState) / (xs - baseline)
				sg = np.sign(stim[2])
				m = sg * np.max(sg * trace[int(t_2 * sr):int(t_steady1 * sr)])
				sag = (m - steadyState) / (baseline - steadyState)
		else:
			tmp = trace * np.sign(stim[2])
			if clamp == 'v':
				Rin = stim[2] / (steadyState - baseline)
				sg = np.sign(stim[2])
				m = sg * np.min(sg * trace[int(t_2 * sr):int(t_steady1 * sr)])
				sag = (m - steadyState) / (baseline - steadyState)
			elif clamp == 'i':
				Rin = (steadyState - baseline) / stim[2]
				m = np.max(trace[int(t_2 * sr):int(t_steady1 * sr)])
				sg = np.sign(stim[2])
				m = sg * np.max(sg * trace[int(t_2 * sr):int(t_steady1 * sr)])
				sag = (m - steadyState) / (baseline - steadyState)
		subProps = pd.DataFrame([[baseline, steadyState, Rin, Rs, Cm, sag, 
			stim[2]]], columns = ["baseline", "steadyState", "Rin", "Rs", 
				"Cm", "Sag", "stimAmp"])
		return subProps

	def batchSubAnalysis(self, protocol, comp, clamp, verbose = 1):
		'''
		Analyze subs in all raw data in a certain subfolder/protocol 
		in current data set. Save all the properties in an intermediate 
		hdf5 file in the working directory. In a DataFrame as
		/sub/protocol/subProps, with cell and trial information as
		indices.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		comp: bool
			Are the Rs and Cm compensated?
		clamp: string
			Voltage (v) clamp or current (i) clamp.
		verbose: int
			Whether to print progress information.
			0 - No output.
			1 - Print cell and trial numbers.
			2 - Plot detected action potentials for inspection.
		'''
		# Detect subs and save properties in file
		# trialProps includes window size and total number of subs
		subProps = []
		for c, t in self.projMan.iterate(protocol):
			if verbose:
				self.prt("Cell", c, "Trial", t)
			trace, sr, stim = self.projMan.loadWave(c, t)
			props = self.subAnalysis(trace, sr, 
					stim, comp, clamp, verbose > 1)
			props["cell"] = c
			props["trial"] = t
			props.set_index(["cell", "trial"], inplace = True)
			subProps.append(props)
			if self.stopRequested():
				return 0
		subProps = pd.concat(subProps, sort = True)
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		store.put("/sub/" + protocol + "/subProps", subProps)
		store.close()

	def aveProps(self, protocol, cells = [], stimRange = []):
		'''
		Calculate average sub properties over trials responding to a 
		stimulation of amplitudes within a range if specified.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.
		stimRange: list, optional
			Range of stimulation amplitudes of the trials, two scalars. 
			Only consider amplitudes is within this range. 
			By default not used.

		Returns
		-------
		aveSubProps: pandas.DataFrame
			DataFrame with averge properties for each cell entry.
		'''
		subProps = pd.read_hdf(self.projMan.workDir + os.sep + "interm.h5",
				"/sub/" + protocol + "/subProps")
		if len(cells):
			subProps = subProps.loc[(cells), :]
		if len(stimRange):
			idx = subProps.index[subProps["stimAmp"] >= stimRange[0] &
					subProps["stimAmp"] < stimRange[1]]
			subProps = subProps.loc[idx, :]
		aveSubProps = subProps.groupby("cell").mean()
		aveSubProps.to_csv(self.projMan.workDir + os.sep + \
				"sub_" + protocol + ".csv")
		return aveSubProps

	def profile(self):
		'''
		Override parent class method.
		'''
		basicParam = {"baseline_start" : "float", 
				"baseline_end": "float",
				"steady_state_start": "float",
				"steady_state_end": "float",
				"fit_start": "float",
				"fit_end": "float",
				"scaleV": "float",
				"scaleI": "float",
				"minTau": "float"}
		prof = [
			{"name": "Subthreshold",
				"pname": "batchSub",
				"foo": self.batchSubAnalysis,
				"param": {"protocol": "protocol",
					"comp": "bool",
					"clamp": "combo,v,i",
					"verbose": "int"}},
			{"name": "Properties", 
				"pname": "aveSub", 
				"foo": self.aveProps,
				"param": {"protocol": "protocol",
					"cells": "intl"}}]
		return basicParam, prof
