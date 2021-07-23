# Analyze action potentials in current clamp, including frequency
# and action potential related properties.

import os
import numpy as np
import pandas as pd
from matplotlib.figure import Figure as mfigure
import matplotlib._color_data as mcd
import matplotlib.lines as mlines
import matplotlib as mpl
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
				"accommAP": {"protocol": '',
					"cells": [1],
					"rateRange": [0., 0.],
					"early_ap": 1,
					"late_ap": 2},
				"rheo": {"protocol": '',
					"cells": []},
				"plotp": {"protocols": [],
					"types": [],
					"cells": [],
					"trials": [],
					"rateRange": [0., 0.],
					"idRange": [0, 0],
					"win": [0, 0.003],
					"errorBar": False,
					"label": "none",
					"magnify": 1}}
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
		slope, amp, threshold, width, rate = [], [], [], [], []
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
				# instantaneous firing rate
				rate.append(sr / (starts[s + 1] - starts[s]))
			else: # last spike
				peak_point = np.argmax(trace[starts[s]:
					starts[s] + int(sr / 100)])  # Assume ap with < 10 ms
				troph_point = np.argmin(trace[starts[s] + peak_point:
					starts[s] + int(sr / 100)])  # Assume ap with < 10 ms
				rate.append(np.nan)
			if peak_point == 0:
				slope.append((trace[starts[s]] - trace[starts[s] - 1]) * sr)
			elif peak_point == 1:
				slope.append((trace[starts[s] + 1] - trace[starts[s]]) * sr)
			else:
				slope.append(np.max(np.diff(trace[starts[s]:
							starts[s] + peak_point])) * sr)
			amp.append(trace[starts[s] + peak_point] - trace[starts[s]])
			threshold.append(trace[starts[s]])
			half = 0.5 * (trace[starts[s] + peak_point] + 
					trace[starts[s]])
			if troph_point == 0:
				print('s', s, 'total', len(starts))
				print('stim', stim)
			if len(np.nonzero(trace[starts[s]:
				starts[s] + peak_point] > half)[0]) == 0:
				width.append((1 + \
						np.nonzero(trace[starts[s] + peak_point:
							starts[s] + peak_point + troph_point] > \
									half)[0][-1]) / sr)
			else:
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
		apProps["rate"] = rate
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
		/AP/protocol/[apProps and trialProps].
		/AP/protocol/apProps has ap properties, each row is one action potential.
		Indices are cell and trial id and the ap id in that trial.
		/AP/protocol/trialProps has rate and sAHP properties, each row is
		one trial and indices are cell and trial id.

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
	
	def accomm(self, protocol, cells = [], rateRange = [0, 0], early_ap = 1,
			late_ap = 2):
		'''
		Calculate average action potential accommondation ratio, using spike 
		trains with firing range in a certain range.

		Parameters
		----------
		protocol: string
			Subfolder/protocol where the spike detection is done.
		cells: array_like, optional
			Ids of cells to include, default is all the cells.
		rateRange: array_like, optional
			Range of firing rates, two scalars. Only consider trials with
			firing rate within this range. By defaut not used.
		early_ap: int, optional
			Id of the early action potential, accommondation ratio is the
			ratio of instantaneous firing rate between late action potential
			and early action potential. Default is 1.
		late_ap: int, optional
			Id of the late action potential.

		Returns
		-------
		aveAccomm: pandas.DataFrame
			DataFrame with averge accommondation ratio for each cell entry.
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
			earlyRate = apProps.loc[apProps["id"] + 1 == early_ap, "rate"]
			lateRate = apProps.loc[apProps["id"] + 1 == late_ap, "rate"]
			rates = pd.merge(earlyRate, lateRate, "outer", left_index = True,
					right_index = True, suffixes = ['_early', '_late'])
			if len(rates):
				rates["ratio"] = rates["rate_early"] / rates["rate_late"]
				print(rates)
				aveAccomm = rates.groupby("cell").mean()
				aveAccomm = aveAccomm.merge(self.projMan.getAssignedType(), 
						"left", "cell")
			else:
				aveAccomm = rates
			aveAccomm.to_csv(self.projMan.workDir + os.sep + \
					"accommondation_" + protocol + ".csv")
			return aveAccomm
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
	
	def apPlot(self, protocols, types = [], cells = [], trials = [], 
			rateRange = [0, 0], idRange = [0, 0], win = [0, 3e-3], 
			errorBar = False, label = "none", magnify = 1):
		'''
		Plot averaged traces of selected action potential traces from 
		selected trials from selected cells.

		Parameters
		----------
		protocols: array_lie
			List of names of protocols with which the selected trial were recorded.
		types: array_like, optional
			Types of cells to select. By default all types are included.
		cells: array_like, optional
			Ids of cells to select. By default all cells are included.
		trials: array_like, optional
			Trials fo select. By default all the trial in the specified protocols.
		rateRange: array_like, optional
			Range of firing rates, two scalars. Only consider trials with
			firing rate within this range. By defaut not used.
		idRange: array_like, optional
			Range of spike id in the trial, two scalars. Only consider
			spikes whose ids is within this range. By default not used.
		win: array_like, optional
			Time window in seconds relative to the action potential start point
			to plot the traces. Default is 3 ms after the start point.
		errorBar: boolean, optional
			Whether to plot error bar. Default is not.
		label: string, optional
			One of "type", "protocol", and "none". The label for 
			each trace. Default is "none", nothing will be labeled.
		magnify: float, optional
			Maginification factor for the image. Default is 1.
		'''
		# Select trials and cells
		trialTables = []
		for p in protocols:
			t = self.projMan.getTrialTable(p, cells, trials, types)
			t["protocol"] = p
			trialTables.append(t)
		trialTable = pd.concat(trialTables).reset_index()
		# Plot storage
		traces = []
		labels = []
		errors = []
		# Load firing rate and action potential time data
		apProps = []
		trialProps = []
		store = pd.HDFStore(self.projMan.workDir + os.sep + "interm.h5")
		for p in protocols:
			trialDataF = "/AP/" + p + "/trialProps"
			apDataF = "/AP/" + p + "/apProps"
			if trialDataF in store.keys() and apDataF in store.keys():
				tp = store.get(trialDataF)
				ap = store.get(apDataF)
				apProps.append(ap)
				trialProps.append(tp)
		store.close()
		if len(trialProps) == 0:
			return 0
		trialProps = pd.concat(trialProps)
		apProps = pd.concat(apProps)
		apProps.reset_index("id", inplace = True)
		apProps["id"] = apProps["id"].astype(int)
		# Average traces
		grp = trialTable.groupby(["type", "protocol"])
		for k, v in grp.groups.items():
			apTraces = []
			cellIds = []
			for c, t in trialTable.loc[v, ["cell", "trial"]].values:
				rate = trialProps.loc[(c, t), "rate"]
				if rateRange[0] >= rateRange[1] or \
						(rateRange[0] < rate and rate <= rateRange[1]):
					tr, sr, stim = self.projMan.loadWave(c, t)
					aps = apProps.loc[(c, t), ["starts", "id"]].values # starts and id
					for s, i in aps:
						if idRange[0] >= idRange[1] or \
								(idRange[0] < i and i <= idRange[1]):
							trace = tr[int(s + win[0] * sr):int(s + win[1] * sr)] - \
									tr[int(s)]
							apTraces.append(trace)
							cellIds.append(c)
			if(len(apTraces)):
				cellApTraces = []  # averaged traces for each cell
				apTraces = np.vstack(apTraces)
				cellIds = np.array(cellIds)
				for c in np.unique(cellIds):
					cellApTraces.append(np.mean(apTraces[cellIds == c], axis = 0))
				traces.append(np.mean(cellApTraces, axis = 0))
			if errorBar:
				if len(cellApTraces) > 2:
					errors.append(np.std(cellApTraces, axis = 0) / 
							np.sqrt(len(cellApTraces)))
				else:
					errors.append([])
			if label != "none":
				labels.append(trialTable.loc[v[0], label])
		# Plotting
		fig = mfigure(
				figsize = [d * magnify for d in mpl.rcParams["figure.figsize"]],
				dpi = 300)
		mpl.rcdefaults()
		mpl.rcParams.update({"font.size": magnify * mpl.rcParams["font.size"]})
		ax = fig.subplots()
		if len(labels):
			uniLabels = list(set(labels))
			# xkcd_colors = list(mcd.XKCD_COLORS.keys())
			t10_colors = ['tab:cyan', 'tab:red', 'tab:blue', 'tab:orange', 
					'tab:green', 'tab:purple', 'tab:brown', 'tab:pink', 
					'tab:gray', 'tab:olive']
			colors = [t10_colors[d % len(t10_colors)] 
				for d in range(len(uniLabels))]
		if len(traces):
			x = np.arange(len(traces[0])) / sr
		for i, t in enumerate(traces):
			if self.stopRequested():
				return 0
			if len(labels):
				ax.plot(x, t, color = colors[uniLabels.index(labels[i])])
				if len(errors) and len(errors[i]):
					f = ax.fill_between(x, t - errors[i], t + errors[i], 
							color = colors[uniLabels.index(labels[i])],
							alpha = 0.2)
					f.set_edgecolor("none")
			else:
				ax.plot(x, t, color = 'k')
				if len(errors) and len(errors[i]):
					f = ax.fill_between(x, t - errors[i], t + errors[i],
							color = 'k', alpha = 0.2)
					f.set_edgecolor("none")
		if len(labels):
			handles = []
			for i, l in enumerate(uniLabels):
				handles.append(mlines.Line2D([], [], color = colors[i], label = l))
			ax.legend(handles = handles, loc = "best")
		fig.savefig(self.projMan.workDir + os.sep + "multi_plot_multi_protocol" + 
				".pdf", dpi = 300)

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
			{"name": "Accommondation", 
				"pname": "accommAP", 
				"foo": self.accomm,
				"param": {"protocol": "protocol",
					"cells": "intl",
					"rateRange": "floatr",
					"early_ap": "int",
					"late_ap": "int"}},
			{"name": "Rheobase", 
				"pname": "rheo", 
				"foo": self.rheobase,
				"param": {"protocol": "protocol",
					"cells": "intl"}},
			{"name": "Plot",
				"pname": "plotp",
				"foo": self.apPlot,
				"param": {"protocols": "strl",
					"types": "strl",
					"cells": "intl",
					"trials": "intl",
					"rateRange": "floatr",
					"idRange": "intr",
					"win": "floatr",
					"errorBar": "bool",
					"label": "combo,type,protocol,none",
					"magnify": "float"}}]
		return basicParam, prof
