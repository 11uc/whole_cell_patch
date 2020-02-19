# Analyze seal tests in voltage or current clamps and calculate 
# related properties including access resistance, input resistance, 
# membrane capacitance. The difference to subthreshold analysis is 
# that the stimulation time and amplitude need to be specified here,
# that the stimulation is usually small so that sag is not 
# considered and that the time parameters are not relative to start
# of stimulation.

import os
import numpy as np
import pandas as pd
from . import plot
from .project import Project
from .analysis import Analysis
from .process import SignalProc

class SealTest(SignalProc, Analysis):
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
				"basic": {"baseline_start" : 0.04,
					"baseline_end": 0.045,
					"steady_state_start": 0.15,
					"steady_state_end": 0.2,
					"seal_test_start": 0.05,
					"fit_end": 0.15,
					"scaleV": 1e12,
					"scaleI": 1e3,
					"ampV": -0.005,
					"ampI": -25e-12,
					"minTau": 1e-3},
				"batchSt": {"protocol": '',
					"comp": False,
					"clamp": 'v',
					"verbose": 0},
				"aveSt": {"protocol": '',
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
		self.stParam = param

	def stAnalysis(self, trace, sr, stim, comp = False, 
			clamp = 'v', verbose = 0):
		'''
		Analyze seat test responses in voltage/current clamp. 

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
		stProps: pandas.DataFrame
			Sub properties, has one row, columns are properties
		'''
		# sub properties
		baseline = 0  # baseline amplitude
		steadyState = 0  # steady state amplitude
		Rin = 0  # input resistance
		Rs = 0	# access resistance
		Cm = 0	# membrane capacitance
		# load parameters
		t_baseline1 =  self.stParam['baseline_start']
		t_baseline2 = self.stParam['baseline_end']
		t_steady1 = self.stParam['steady_state_start']
		t_steady2 = self.stParam['steady_state_end']
		t_0 = self.stParam['seal_test_start']
		t_2 = self.stParam['fit_end']
		if clamp == 'v':  # voltage clamp
			scale = self.stParam["scaleV"]	# scale up for better fitting
			amp = self.stParam["ampV"]
			# fit start time is the peak after seal test start
			t_1 = np.argmax(trace[int(t_0 * sr):int(t_steady1 * sr)] * \
					np.sign(amp)) / sr + t_0
		else:  # current clamp
			scale = self.stParam["scaleI"]
			amp = self.stParam["ampI"]
			# start of curve fit, assume charging of pipette 
			# capacitance takes no time
			t_1 = t_0
		minTau = self.stParam["minTau"]  # minimum tau accepted
		# Amplitude parameters
		# Steady state current is the final steady state after sag
		# current stablized.
		steadyState = np.mean(trace[int(t_steady1 * sr):
			int(t_steady2 * sr)]) / scale
		# Baseline current before stimulation 
		baseline = np.mean(trace[int(t_baseline1 * sr):
			int(t_baseline2 * sr)]) / scale

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
						int(t_1 * sr), int(t_2 * sr), np.sign(amp))
				if verbose or tau < minTau:
					verbose = True
					self.prt('I0 = ', x0)
					self.prt('tau = ', tau)
					self.prt('Is = ', xs)

					pt1 = int(t_0 * sr)
					pt2 = int(t_2 * sr)
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
			except ValueError:
				self.prt("Wrong input format.")
			except TypeError:
				self.prt("Fitting Error.")
				trapped = False
				raise
		if trapped:  # fit accepted
			if clamp == 'v':
				Rs = amp / (x0 - baseline)
				Rin = amp / (xs - baseline) - Rs
				Cm = tau * (Rin + Rs) / Rin / Rs
			elif clamp == 'i':
				Rs = (x0 - baseline) / amp
				Rin = (xs - baseline) / amp - Rs
				Cm = tau / Rin
		else:
			tmp = trace * np.sign(amp)
			if clamp == 'v':
				Rin = amp / (steadyState - baseline)
			elif clamp == 'i':
				Rin = (steadyState - baseline) / amp
		stProps = pd.DataFrame([[Rin, Rs, Cm]], columns = ["Rin", "Rs", "Cm"])
		return stProps

	def batchStAnalysis(self, protocol, comp, clamp, verbose = 1):
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
		stProps = []
		for c, t in self.projMan.iterate(protocol):
			if verbose:
				self.prt("Cell", c, "Trial", t)
			trace, sr, stim = self.projMan.loadWave(c, t)
			props = self.stAnalysis(trace, sr, 
					stim, comp, clamp, verbose > 1)
			props["cell"] = c
			props["trial"] = t
			props.set_index(["cell", "trial"], inplace = True)
			stProps.append(props)
			if self.stopRequested():
				return 0
		stProps = pd.concat(stProps, sort = True)
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		store.put("/st/" + protocol + "/stProps", stProps)
		store.close()

	def aveProps(self, protocol, cells = []): 
		'''
		Calculate average sub properties over trials responding to a 
		stimulation of amplitudes within a range if specified.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.

		Returns
		-------
		aveSubProps: pandas.DataFrame
			DataFrame with averge properties for each cell entry.
		'''
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		dataF = "/sub/" + protocol + "/stProps"
		if dataF in store.keys():
			stProps = store[dataF]
			store.close()
			if len(cells):
				cells = list(set(cells) & 
						set(self.projMan.getSelectedCells()) &
						set(stProps.index.get_level_values["cell"]))
				stProps = stProps.loc[(cells), :]
			aveStProps = stProps.groupby("cell").mean()
			aveStProps= aveStProps.merge(self.projMan.getAssignedType(), 
					"left", "cell")
			aveStProps.to_csv(self.projMan.workDir + os.sep + \
					"st_" + protocol + ".csv")
			return aveStProps
		store.close()

	def profile(self):
		'''
		Override parent class method.
		'''
		basicParam = {"baseline_start" : "float",
				"baseline_end": "float",
				"steady_state_start": "float",
				"steady_state_end": "float",
				"seal_test_start": "float",
				"fit_end": "float",
				"scaleV": "float",
				"scaleI": "float",
				"ampV": "float",
				"ampI": "float",
				"minTau": "float"}
		prof = [
			{"name": "Seal Test",
				"pname": "batchSt",
				"foo": self.batchStAnalysis,
				"param": {"protocol": "protocol",
					"comp": "bool",
					"clamp": "combo,v,i",
					"verbose": "int"}},
			{"name": "Properties", 
				"pname": "aveSt", 
				"foo": self.aveProps,
				"param": {"protocol": "protocol",
					"cells": "intl"}}]
		return basicParam, prof
