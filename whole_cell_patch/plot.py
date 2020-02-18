# Plotting functions

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters

def plot_trace(trace, sr, smooth_trace = None , points = None, stim = None, \
		shift = [], cl = 'k', pcl = 'b', win = None, ax = None): 
	'''
	Plot recorded traces with PyQtGraph.
	Parameters
	----------
	trace: array_like
		Time sequence of recorded signal.
	sr: float
		Sampling rate.
	smooth_trace: array_like, optional
		Smoothed trace, plot in the same axis if it's not None. Default
		is None.
	points: array_like, optional
		Time points to hightlight on the trace if it's not None. Default
		is None.
	win: array_like, optional
		A pair of two scalars, time window of the trace to plot. If 
		it's None, plot the entire trace. Default is None.
	stim: array_like. optional
		Stimulation time points. If not None, plot tiny verticle bars 
		to indicate stimulation time points.
	shift: array_like, optional
		Two scalars indicating shift on the x and y axes. Default is 
		empty, won't shift.
	cl: Any parameters accepted by pyqtgraph.mkPen(). Optional.
		Color of the trace, optional, default is black.
	pcl: Any parameters accepted by pyqtgraph.mkPen(). Optional.
		Color of the point symbols, optional, default is blue.
	ax: pyqtgraph.PlotDataItem, optional.
		Axis to plot the trace in. Default is none, in which case a new object
		will be created.
	Return
	------
	ax: pyqtgraph.PlotDataItem
		Pyqtgraph PlotDataItem that could be displayed in a plotWidget.
	'''

	t = np.arange(len(trace)) / sr
	if len(shift):
		t = t + shift[0]
		trace = trace + shift[1]
	if win is None:
		win = [0, len(trace)]
	else:
		win = [int(d * sr) for d in win]
	if ax == None:
		ax = pg.PlotWidget()
	ax.plot(t[win[0]:win[1]], trace[win[0]:win[1]], pen = cl)
	if smooth_trace is not None:
		ax.plot(t[win[0]:win[1]], smooth_trace[win[0]:win[1]], pen = 'g')
	if points is not None and len(points):
		points = (np.array(points) * sr).astype(int)
		points_in = points[(win[0] < points) * (points < win[1])]
		ax.plot(t[points_in], trace[points_in], pen = None, \
				symbol = 'o', symbolBrush = pcl)
	if stim is not None:
		yr = max(trace) - min(trace)
		for st in stim:
			y1 = trace[int(st / sr)] - 0.1 * yr
			y2 = trace[int(st / sr)] + 0.1 * yr
			ax.plot([st, st], [y1, y2], pen = pg.mkPen('k')) 
	return ax

def save_fig(ax, name):
	'''
	Save figures made from plot_trace in a file.

	Parameters
	----------
	ax: pyqtgraph.PlotDataItem
		Axis to save.
	name: string
		Name of the output file.
	'''
	exporter = pg.exporters.ImageExporter(ax.getPlotItem())
	exporter.parameters()["width"] = 100
	exporter.export(name)
