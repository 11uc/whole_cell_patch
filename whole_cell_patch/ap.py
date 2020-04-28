# Analyze action potentials in current clamp, including frequency
# and action potential related properties.

import os
import numpy as np
import pandas as pd
from .project import Project
from .analysis import Analysis
from . import plot

class AP(Analysis):
	'''
	Analyzing properties related to action potentials, including
	AHP and firing rate.
	'''
	def __init__(self, inTxtWidget, projMan = None, parent = None):
		'''
		Load spike detection parameters from the grand parameter file
		and raw data information.

		Parameters
		----------
		inTxtWidget: QLineEdit
			Input line widget of the main window.
		projMan: Project
			Object containing information about the project including 
			raw data and some parameters.
		'''
		super().__init__(inTxtWidget, projMan, parent)

	def loadDefault(self, name):
		'''
		Override parent class method.
		'''
		default = {
				"basic": {"spike_slope_threshold": 20.,
					"spike_peak_threshold": 0.02,
					"half_width_threshold": 0.004,
					"sign": 1,
					"mAHP_begin": 0.01,
					"mAHP_end": 0.2,
					"baseline": 0.1,
					"sAHP_begin": 0.2,
					"sAHP_end": 0.5},
				"batchAP": {"protocol": '',
					"verbose": 0},
				"fr": {"protocol": '',
					"cells": [1],
					"stims": [0.1]},
				"aveAP": {"protocol": '',
					"cells": [1],
					"rateRange": [0., 0.],
					"idRange": [0, 0]},
				"rheo": {"protocol": '',
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
		self.spikeDetectParam = {}
		for k in ["spike_slope_threshold", "spike_peak_threshold", 
				"half_width_threshold", "sign"]:
			self.spikeDetectParam[k] = param[k]
		self.AHPParam = {}
		for k in ["mAHP_begin", "mAHP_end", "baseline", 
				"sAHP_begin", "sAHP_end"]:
			self.AHPParam[k] = param[k]

	def spikeAnalysis(self, trace, sr, stim, plotting = False): 
		'''
		Detect action potential spikes and analyze related properties.  Find 
		start time of spikes by finding point with slope over slope_th 
		followed by a peak of relative amplitude above peak_th.  The peak is 
		defined as the first point reversing slope after the start point. 
		Only look at time period when there's stimulation.

		Parameters
		----------
		trace: numpy.array
			Voltage trace.
		sr: float
			Sampling rate.
		stim: list
			Stimulation information of the trace.
		plotting: boolean, optional
			Whether to plot the trace with starting point marked for
			inspection. Default is not.

		Returns
		-------
		apProps: pandas.DataFrame
			Action potential properties, row are action potentials 
			in the trial and columns are properties
		trialProps: dictionary
			Properties for the trials, including sAHP propeties.
		'''
		apProps = pd.DataFrame()
		trialProps = {}
		# Parameters used for spike detection
		slope_th = self.spikeDetectParam['spike_slope_threshold']
		peak_th = self.spikeDetectParam['spike_peak_threshold']
		width_th = self.spikeDetectParam['half_width_threshold']
		sign = self.spikeDetectParam['sign']
		if sign < 0:
			trace = trace * sign
		trace_diff = np.diff(trace) * sr
		pstart = np.nonzero(trace_diff > slope_th)[0]  # possible start points
		reverse = np.nonzero(trace_diff < 0)[0] # possible peak points
		starts = []
		i = 0  # index in pstart
		j = 0  # index in reverse
		while i < len(pstart) and j < len(reverse) and \
				pstart[i] < sr * (stim[0] + stim[1]):
			if pstart[i] < sr * stim[0]:
				i += 1
			elif pstart[i] < reverse[j]:
				if peak_th < trace[reverse[j]] - trace[pstart[i]] and \
					reverse[j] - pstart[i] < width_th * sr:
					starts.append(pstart[i])
					while i < len(pstart) and pstart[i] < reverse[j]:
						i += 1
				else:
					i += 1
			else:
				j += 1
		apProps["starts"] = starts  # indices of begin of peaks
		# plot trace with spike start points marked if needed
		if plotting:
			ax = plot.plot_trace_buffer(trace, sr, points = np.array(starts) / sr)
			self.plt(ax)
			ans = self.ipt("Good? (y/n, y to continue, n to abort)")
			if ans == 'n' or ans == 'N':
				return None, None
		# Then calculate properties slope, amp, threshold, width
		slope, amp, threshold, width = [], [], [], []
		# and mAHP amplitudes
		mAHP = np.full(len(starts), np.nan)
		# Parameters used for mAHP calculation
		mAHPb = self.AHPParam["mAHP_begin"]
		mAHPe = self.AHPParam["mAHP_end"]
		for s in range(len(starts)):
			if s < len(starts) - 1: # spikes ahead of the last one
				# peak point relative the start point
				peak_point = np.argmax(trace[starts[s]:starts[s + 1]])
				# troph point after peak relative to the peak point
				troph_point = np.argmin(trace[starts[s] + peak_point:
					starts[s + 1]])
				if starts[s] + sr * mAHPb < starts[s + 1]:
					mAHP[s] = trace[starts[s]] - np.min(trace[int(mAHPb * sr):
						min(starts[s] + int(mAHPe * sr), starts[s + 1])])
			else: # last spike
				peak_point = np.argmax(trace[starts[s]:
					starts[s] + int(sr / 100)])  # Assume ap with < 10 ms
				troph_point = np.argmin(trace[starts[s] + peak_point:
					starts[s] + int(sr / 100)])  # Assume ap with < 10 ms
			slope.append(np.max(np.diff(trace[starts[s]:
						starts[s] + peak_point])) * sr)
			amp.append(trace[starts[s] + peak_point] - trace[starts[s]])
			threshold.append(trace[starts[s]])
			half = 0.5 * (trace[starts[s] + peak_point] + 
					trace[starts[s]])
			if troph_point == 0:
				print('s', s, 'total', len(starts))
				print('stim', stim)
			width.append((peak_point - np.nonzero(trace[starts[s]:
						starts[s] + peak_point] > half)[0][0] + \
					np.nonzero(trace[starts[s] + peak_point:
						starts[s] + peak_point + troph_point] > \
								half)[0][-1]) / sr)
		apProps["slope"] = slope
		apProps["amp"] = amp
		apProps["threshold"] = threshold
		apProps["width"] = width
		apProps["mAHP"] = mAHP
		# Lastly, the sAHP or end of pulse AHP
		baseline = self.AHPParam["baseline"]
		sAHPb = self.AHPParam["sAHP_begin"]
		sAHPe = self.AHPParam["sAHP_end"]
		baselineAmp = np.mean(trace[int((stim[0] - baseline) * sr):
			int(stim[0] * sr)])
		trialProps["sAHP"] = baselineAmp - \
				np.mean(trace[int((stim[0] + stim[1] + sAHPb) * sr):\
				int((stim[0] + stim[1] + sAHPe) * sr)])
		# and firing rate and stimulation amplitude
		trialProps["stimAmp"] = stim[2]
		trialProps["rate"] = len(apProps) / stim[1]
		return apProps, pd.DataFrame(trialProps, index = [0])

	def batchSpikeAnalysis(self, protocol, verbose = 1):
		'''
		Analyze action potential spikes in all raw data in a certain 
		subfolder/protocol in current data set. Save all the properties
		in an intermediate hdf5 file in the working directory. In group
		/AP/protocol/[apProps and trialProps]

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		verbose: int
			Whether to print progress information.
			0 - No output.
			1 - Print cell and trial numbers.
			2 - Plot detected action potentials for inspection.
		
		Returns
		-------
		ret: int
			Return state.
			1 - Normally finished.
			0 - User interupted.
		'''
		apProps = []
		trialProps = []
		for c, t in self.projMan.iterate(protocol):
			if verbose:
				self.prt("Cell", c, "Trial", t)
			trace, sr, stim = self.projMan.loadWave(c, t)
			ap, trial = self.spikeAnalysis(trace, sr, 
					stim, verbose > 1)
			if verbose > 1 and ap is None:
				return 0
			ap.index.name = "id"
			ap["cell"] = c
			ap["trial"] = t
			ap.set_index(["cell", "trial"], append = True, inplace = True)
			apProps.append(ap)
			trial["cell"] = c
			trial["trial"] = t
			trial.set_index(["cell", "trial"], inplace = True)
			trialProps.append(trial)
			if self.stopRequested():
				return 0
		apProps = pd.concat(apProps, sort = True)
		trialProps = pd.concat(trialProps, sort = True)
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		store.put("/AP/" + protocol + "/apProps", apProps, "table")
		store.put("/AP/" + protocol + "/trialProps", trialProps, "table")
		store.close()
		return 1

	def aveFiringRate(self, protocol, cells = [], stims = []):
		'''
		Calculate average firing rate of trials with the same stimulation
		amplitude.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.
		stims: array_like, optional
			Amplitude of stimulations to include, default is all the trials.

		Returns
		-------
		firingRates: pandas.DataFrame
			DataFrame with average firing rate, with multiindex of 
			["cell", "stimAmp"].
		'''
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		dataF = "/AP/" + protocol + "/trialProps"
		if dataF in store.keys():
			trialProps = store[dataF]
			firingRates = trialProps.groupby(["cell", "stimAmp"]).mean()
			if len(cells):
				cells = list(set(cells) &
						set(self.projMan.getSelectedCells()) &
						set(trialProps.index.get_level_values("cell")))
				firingRates = firingRates.loc[(cells), :]
			if len(stims):
				firingRates = firingRates.loc[(slice(None), stims), :]
			# Save the average data in a csv file, could be accessed by 
			# users for further analysis, also could be used for further
			# plotting and statistic analysis.
			firingRates= firingRates.join(self.projMan.getAssignedType(), "cell",
					"left")
			firingRates.to_csv(self.projMan.workDir + os.sep + \
					"fr_" + protocol + ".csv")
			store.close()
			return firingRates
		store.close()

	def aveProps(self, protocol, cells = [], rateRange = [0, 0], 
			idRange = [0, 0]):
		'''
		Calculate average action potential properties, including AHP 
		properties, using spike trains with firing range in a certain
		range and action potentials from those trials of indices in 
		a certain range.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.
		rateRange: array_like, optional
			Range of firing rates, two scalars. Only consider trials with
			firing rate within this range. By defaut not used.
		idRange: array_like, optional
			Range of spike id in the trial, two scalars. Only consider
			spikes whose ids is within this range. By default not used.

		Returns
		-------
		aveAPProps: pandas.DataFrame
			DataFrame with averge properties for each cell entry.
		'''
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		trialDataF = "/AP/" + protocol + "/trialProps"
		apDataF = "/AP/" + protocol + "/apProps"
		if trialDataF in store.keys() and apDataF in store.keys():
			trialProps = store.get(trialDataF)
			apProps = store.get(apDataF)
			apProps.reset_index("id", inplace = True)
			apProps["id"] = apProps["id"].astype(int)
			store.close()
			if len(cells):
				cells = list(set(cells) &
						set(self.projMan.getSelectedCells()) &
						set(apProps.index.get_level_values("cell")))
				apProps = apProps.loc[(cells), :]
			if rateRange[0] < rateRange[1]:
				idx = trialProps.index[(trialProps["rate"] >= rateRange[0]) &
						(trialProps["rate"] < rateRange[1])]
				if len(idx):
					apProps = apProps.loc[idx, :]
				else:
					apProps = pd.DataFrame([], columns = apProps.columns,
							index = idx)
			if idRange[0] < idRange[1] and len(apProps):
				'''
				idx = apProps.index[(apProps["id"] + 1 >= idRange[0]) &
						(apProps["id"] + 1 < idRange[1])]
				if len(idx):
					apProps = apProps.loc[idx, :]
				else:
					apProps = pd.DataFrame([], columns = apProps.columns,
							index = idx)
				'''
				apProps = apProps.iloc[list((apProps["id"] + 1 >= idRange[0]) &
						(apProps["id"] + 1 < idRange[1])), :]
			if len(apProps):
				aveAPProps = apProps.groupby("cell").mean()
				aveAPProps= aveAPProps.merge(self.projMan.getAssignedType(), 
						"left", "cell")
			else:
				aveAPProps = apProps
			aveAPProps.to_csv(self.projMan.workDir + os.sep + \
					"ap_" + protocol + ".csv")
			return aveAPProps
		store.close()
	
	def rheobase(self, protocol, cells = []):
		'''
		Find the rheobase, minimum amount of current required for the
		cell to fire, for each cell.

		Parameters
		----------
		protocol: string
			Protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.
		'''
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		dataF = "/AP/" + protocol + "/trialProps"
		if dataF in store.keys():
			trialProps = store[dataF]
			rb = trialProps.loc[trialProps["rate"] > 0].groupby("cell").min()
			if len(cells):
				cells = list(set(cells) &
						set(self.projMan.getSelectedCells()) &
						set(trialProps.index.get_level_values("cell")))
				rb = rb.loc[(cells), :]
			rb.to_csv(self.projMan.workDir + os.sep + \
					"rheo_" + protocol + ".csv")
		store.close()

	def profile(self):
		'''
		Override parent class method.
		'''
		basicParam = {"spike_slope_threshold": "float",
				"spike_peak_threshold": "float",
				"half_width_threshold": "float",
				"sign": "int",
				"mAHP_begin": "float",
				"mAHP_end": "float",
				"baseline": "float",
				"sAHP_begin": "float",
				"sAHP_end": "float"}
		prof = [
			{"name": "Spike Detect",
				"pname": "batchAP",
				"foo": self.batchSpikeAnalysis,
				"param": {"protocol": "protocol",
					"verbose": "int"}},
			{"name": "Firing Rate", 
				"pname": "fr", 
				"foo": self.aveFiringRate,
				"param": {"protocol": "protocol",
					"cells": "intl",
					"stims": "floatl"}},
			{"name": "Properties", 
				"pname": "aveAP", 
				"foo": self.aveProps,
				"param": {"protocol": "protocol",
					"cells": "intl",
					"rateRange": "floatr",
					"idRange": "intr"}},
			{"name": "Rheobase", 
				"pname": "rheo", 
				"foo": self.rheobase,
				"param": {"protocol": "protocol",
					"cells": "intl"}}]
		return basicParam, prof
