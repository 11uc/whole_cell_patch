# Analysis module plotting raw data from multiple conditioned
# simultaneously.

import os
import numpy as np
import pandas as pd
from matplotlib.figure import Figure as mfigure
import matplotlib._color_data as mcd
import matplotlib.lines as mlines
import matplotlib as mpl
from .project import Project
from .process import SignalProc
from .analysis import Analysis
from . import plot

class MultiPlot(Analysis):
	'''
	Module used to plot multiple traces more efficiently.
	'''
	def __init__(self, inTxtWidget, projMan = None, parent = None):
		'''
		Initialize.

		Parameters
		----------
		inTxtWidget: QLineEdit
			Input line widget of the main window.
		projMan: Project
			Object containing information about the project including 
			raw data and some parameters.
		'''
		Analysis.__init__(self, inTxtWidget, projMan, parent)

	def loadDefault(self, name):
		'''
		Override parent class method.
		'''
		default = {
				"basic": {},
				"mpPlot": {"protocol": "protocol",
					"types": [],
					"cells": [],
					"stims": [],
					"trials": [],
					"aveLevel": "none",
					"label1": "none",
					"label2": "none",
					"normWin": [0, 0],
					"win": [0, 0],
					"errorBar": False,
					"magnify": 1}}
		return default[name]

	def setBasic(self, param):
		'''
		This module doesn't use basic parameters.
		'''
		self.mpParam = {}

	def avePlot(self, protocol, types, cells, stims, trials, aveLevel, 
			label1, label2, normWin, win, errorBar, magnify):
		'''
		Plotting raw data trace across type, cell, stimulation amplitude
		and trials. Cell and trials could be averaged. If average is taken 
		at both the cell and trial levels, 
		of the highest level. If the level to label on is averaged,
		there will be no labels.

		Parameters
		----------
		protocol: string
			Protocol trials from which will be plotted.
		types: array_like
			Types of cells to include. Include all the cells when empty.
		cells: array_like
			Ids of cells to include. Include all the cells when empty.
		stims: array_like
			Stimulation amplitudes with which trials will be included.
			Include all trials when empty.
		trials: array_like
			Ids of trials to include. Include all the trials when empty.
		aveLevel: string
			One of "cells", "trials" and "none".
			"cells" - 
				Average cells and trials. Trials will be averaged first 
				and error bar will consider sample size of cells if there 
				is more than one cells, otherwise trials number will be
				used.
			"trials" -
				Only average trials.
			"none" -
				Plot individual trials without averaging.
		label1: string
			One of "type", "cell", "stim", "trial", and "none". Part 1 of
			the label for each trace. If "none", nothing will be labeledl.
		label2: string
			One of "type", "cell", "stim", "trial", and "none". Part 2 of
			the label for each trace, if "none", only part 1 will be used.
		normWin: list
			Of two scalars, time window of trace used as baseline to
			normalize the traces. Won't be applied if not valid.
		win: list
			Of two scalars, time window within which the traces will be plot.
			Won't be applied if not valid.
		errorBar: bool
			Whether to plot error bar. If sample size is smaller than 3,
			won't be plotted even when this value is true.
		magnify: float, optional
			Maginification factor for the image. Default is 1.
		'''
		trialTable = self.projMan.getTrialTable(protocol, cells, trials,
			types, stims)
		traces = []
		labels = []
		errors = []
		if aveLevel == "none":
			for i in range(len(trialTable)):
				c, t = trialTable.loc[i, ["cell", "trial"]]
				tr, sr, stim = self.projMan.loadWave(c, t)
				if 0 <= normWin[0] and normWin[0] < normWin[1] and \
						normWin[1] * sr < len(tr):
					trace = tr - np.mean(
							tr[int(normWin[0] * sr):int(normWin[1] * sr)])
				else:
					trace = tr
				if 0 < win[0] and win[0] < win[1] and win[1] * sr < len(trace):
					trace = trace[int(win[0] * sr):int(win[1] * sr)]
				traces.append(trace)
				if label1 != "none":
					if label2 != "none" and label2 != label1:
						labels.append("{0} {1}, {2} {3}".format(
									label1, trialTable.loc[i, label1],
									label2, trialTable.loc[i, label2]))
					else:
						labels.append("{0} {1}".format(label1,
									trialTable.loc[i, label1]))
		elif aveLevel == "trials" or len(np.unique(trialTable["cell"])) == 1:
			grp = trialTable.groupby(["stim", "cell"])
			for k, v in grp.groups.items():
				tTraces = []
				for c, t in trialTable.loc[v, ["cell", "trial"]].values:
					tr, sr, stim = self.projMan.loadWave(c, t)
					if 0 <= normWin[0] and normWin[0] < normWin[1] and \
							normWin[1] * sr < len(tr):
						trace = tr - np.mean(
								tr[int(normWin[0] * sr):int(normWin[1] * sr)])
					else:
						trace = tr
					if 0 < win[0] and win[0] < win[1] and win[1] * sr < len(trace):
						trace = trace[int(win[0] * sr):int(win[1] * sr)]
					tTraces.append(trace)
				traces.append(np.mean(tTraces, axis = 0))
				if errorBar:
					if len(v) > 2:
						errors.append(np.std(tTraces, axis = 0) /
								np.sqrt(len(v)))
					else:
						errors.append([])
				if aveLevel == "trials":
					if label1 != "none" and label1 != "trial":
						if label2 != "none" and label2 != "trial" and \
								label2 != label1:
							labels.append("{0} {1}, {2} {3}".format(
									label1, trialTable.loc[v[0], label1],
									label2, trialTable.loc[v[0], label2]))
						else:
							labels.append("{0} {1}".format(label1,
									trialTable.loc[v[0], label1]))
				else:
					if label1 == "type" or label1 == "stim":
						if (label2 == "type" or label2 == "stim") and \
								label2 != label1:
							labels.append("{0} {1}, {2} {3}".format(
									label1, trialTable.loc[v[0], label1],
									label2, trialTable.loc[v[0], label2]))
						else:
							labels.append("{0} {1}".format(label1,
									trialTable.loc[v[0], label1]))
		else:
			grp = trialTable.groupby(["type", "stim"])
			for k, v in grp.groups.items():
				tTraces = []
				for c, t in trialTable.loc[v, ["cell", "trial"]].values:
					tr, sr, stim = self.projMan.loadWave(c, t)
					if 0 <= normWin[0] and normWin[0] < normWin[1] and \
							normWin[1] * sr < len(tr):
						trace = tr - np.mean(
								tr[int(normWin[0] * sr):int(normWin[1] * sr)])
					else:
						trace = tr
					if 0 < win[0] and win[0] < win[1] and win[1] * sr < len(trace):
						trace = trace[int(win[0] * sr):int(win[1] * sr)]
					tTraces.append(trace)
				cgrp = trialTable.loc[v, ["cell", "trial"]].reset_index(
						drop = True).groupby("cell")
				tTraces = np.vstack(tTraces)
				cTraces = []
				for ck, cv in cgrp.groups.items():
					cTraces.append(np.mean(tTraces[cv], axis = 0))
				traces.append(np.mean(cTraces, axis = 0))
				if errorBar:
					if len(cv) > 2:
						errors.append(np.std(cTraces, axis = 0) /
								np.sqrt(len(cv)))
					else:
						errors.append([])
				if label1 == "type" or label1 == "stim":
					if (label2 == "type" or label2 == "stim") and label2 != label1:
						labels.append("{0} {1}, {2} {3}".format(
									label1, trialTable.loc[v[0], label1],
									label2, trialTable.loc[v[0], label2]))
					else:
						labels.append("{0} {1}".format(label1,
									trialTable.loc[v[0], label1]))
		fig = mfigure(
				figsize = [d * magnify for d in mpl.rcParams["figure.figsize"]],
				dpi = 300)
		mpl.rcdefaults()
		mpl.rcParams.update({"font.size": magnify * mpl.rcParams["font.size"]})
		ax = fig.subplots()
		if len(labels):
			uniLabels = list(set(labels))
			# xkcd_colors = list(mcd.XKCD_COLORS.keys())
			t10_colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 
					'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 
					'tab:olive', 'tab:cyan']
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
		fig.savefig(self.projMan.workDir + os.sep + "multi_plot_" + 
				protocol + ".pdf", dpi = 300)
	
	def profile(self):
		'''
		Return the profile of this module so that the gui could display
		the parameters and the functions.

		Returns
		-------
		basicParam: dictionary
			This module doesn't use basic parameters.
		prof: list of dictionaries
			The profile for functions. Each dictionary describe one function.
			The key : value pairs are:
			- "name" : name of the function
			- "pname" : name of the parameter dictionary key
			- "foo" : the function that could be called
			- "param" : parameter types, same format as the basicParam
		'''
		basicParam = {}
		prof = [
			{"name": "Multi-trace plot",
				"pname": "mpPlot",
				"foo": self.avePlot,
				"param": {"protocol": "protocol",
					"types": "strl",
					"cells": "intl",
					"stims": "floatl",
					"trials": "intl",
					"aveLevel": "combo,cells,trials,none",
					"label1": "combo,type,cell,stim,trial,none",
					"label2": "combo,type,cell,stim,trial,none",
					"normWin": "floatr",
					"win": "floatr",
					"errorBar": "bool",
					"magnify": "float"}}]
		return basicParam, prof
