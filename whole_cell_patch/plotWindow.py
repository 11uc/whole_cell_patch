# Window used to plot data

from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtWidgets import QDialog, QPushButton, QGridLayout, QLabel, \
		QVBoxLayout, QHBoxLayout, QLineEdit, QGridLayout
import pyqtgraph as pg
import numpy as np
from . import plot
from .scaleBar import ScaleBar

class PlotWindow(QDialog):
	'''
	Window containing pyqtgraph.PlotWidget to display plots,
	including raw trace data.
	'''
	# Signals sent to main window for managing plot windows
	focusInSig = pyqtSignal()
	closeSig = pyqtSignal()

	def __init__(self, parent = None):
		'''
		Initialize and setup the window.

		Attributes
		----------
		traces: dictionary
			Plots made in the current window with name as key.
		'''
		super().__init__(parent)
		self.setModal(False)
		# buttons and boxes used for manipulating the graph
		legendBtn = QPushButton("Legend")
		axisBtn = QPushButton("Axis")
		crosshairBtn = QPushButton("Crosshair")
		scaleBtn = QPushButton("ScaleBar")
		self.xbarLe = QLineEdit(self)
		xbarHB = QHBoxLayout()
		xbarHB.addWidget(QLabel('x'))
		xbarHB.addWidget(self.xbarLe)
		self.ybarLe = QLineEdit(self)
		ybarHB = QHBoxLayout()
		ybarHB.addWidget(QLabel('y'))
		ybarHB.addWidget(self.ybarLe)
		btnGrid = QGridLayout()
		gridItems = [legendBtn, axisBtn, crosshairBtn, 
				scaleBtn, xbarHB, ybarHB]
		gridPos = [(i, j) for i in range(2) for j in range(3)]
		for item, p in zip(gridItems, gridPos):
			if type(item) is QHBoxLayout:
				btnGrid.addLayout(item, *p)
			else:
				btnGrid.addWidget(item, *p)
		topVB = QVBoxLayout(self)
		self.plotW = pg.PlotWidget(self, background = "w")
		self.plotI = self.plotW.getPlotItem()
		self.status = QLabel('')
		self.status.setWordWrap(True)
		self.coorTxt = ''
		topVB.addWidget(self.status)
		topVB.addWidget(self.plotW)
		topVB.addLayout(btnGrid)
		self.traces = {}
		self.colors = {}
		self.legend = None
		self.axisOn = True
		self.crosshairOn = False
		self.scaleBar = None
		self.vLine = pg.InfiniteLine(angle=90, movable=False)
		self.hLine = pg.InfiniteLine(angle=0, movable=False)
		self.proxy = pg.SignalProxy(self.plotI.scene().sigMouseMoved, 
				rateLimit=60, slot=self.mouseMoved)
		self.vb = self.plotI.vb
		legendBtn.clicked.connect(self.toggleLegend)
		axisBtn.clicked.connect(self.toggleAxis)
		crosshairBtn.clicked.connect(self.toggleCrosshair)
		scaleBtn.clicked.connect(self.toggleScaleBar)
		self.show()

	def plot(self, *args, **kargs):
		'''
		Pass parameters to PlotItem.plot to make plots in the PlotItem
		in this window and keep track of plots.

		Parameters
		----------
		Same as PlotItem.plot, besides that name has default value, the
		string of the id of the plot that's being made.
		'''
		name = kargs.get("name", str(len(self.traces)))
		kargs["name"] = name
		kargs["pen"] = 'k'
		self.colors[name] = "#000000"
		self.traces[name] = self.plotI.plot(*args, **kargs)
		self.update()

	def remove(self, name):
		'''
		Remove a trace from current window.

		Parameters
		----------
		name: string
			Name of the trace to be removed.
		'''
		if name in self.traces:
			self.plotI.removeItem(self.traces.pop(name))
			self.colors.pop(name)
		self.update()

	def toggleLegend(self):
		'''
		Toggle display of the legend. When on, display traces in 
		different colors.
		'''
		if self.legend == None:
			self.legend = self.plotI.addLegend()
			i = 0
			for k, t in self.traces.items():
				cl = pg.intColor(i, len(self.traces))
				t.setPen(cl)
				self.colors[k] = '#' + pg.colorStr(cl)[:-2]
				self.legend.addItem(t, t.name())
				i = i + 1
		else:
			for k, t in self.traces.items():
				t.setPen('k')
				self.colors[k] = "#000000"
			self.vb.removeItem(self.legend)
			del(self.legend)
			self.legend = None
			self.plotI.legend = None
		self.update()
	
	def toggleAxis(self):
		'''
		Toggle display of the axes.
		'''
		if self.axisOn:
			self.plotI.showAxis("left", False)
			self.plotI.showAxis("bottom", False)
			self.axisOn = False
		else:
			self.plotI.showAxis("left", True)
			self.plotI.showAxis("bottom", True)
			self.axisOn = True
		self.update()
	
	def toggleCrosshair(self):
		'''
		Toggle display of crosshair and showing the coordinates of the 
		crosshair and the y values of the traces.
		'''
		if self.crosshairOn:
			self.crosshairOn = False
			self.plotI.removeItem(self.vLine)
			self.plotI.removeItem(self.hLine)
		else:
			self.plotI.addItem(self.vLine, ignoreBounds=True)
			self.plotI.addItem(self.hLine, ignoreBounds=True)
			self.crosshairOn = True
		self.update()
	
	def toggleScaleBar(self):
		'''
		Toggle display of scale bar, update scale bar length only when
		toggled on.
		'''
		if self.scaleBar is None:
			try:
				xl = float(self.xbarLe.text())
				yl = float(self.ybarLe.text())
				self.scaleBar = ScaleBar(xl, yl, self.plotI.vb, 
						brush = pg.mkBrush('k'), offset = (30, 30))
			except ValueError:
				self.xbarLe.setText('')
				self.ybarLe.setText('')
		else:
			self.plotI.vb.removeItem(self.scaleBar)
			del self.scaleBar
			self.scaleBar = None
	
	def mouseMoved(self, event):
		'''
		Handle mouse move event only when the crosshair is on.
		'''
		pos = event[0]
		if self.crosshairOn:
			if self.plotI.sceneBoundingRect().contains(pos):
				mousePoint = self.vb.mapSceneToView(pos)
				self.coorTxt = ''
				for k, t in self.traces.items():
					data = t.getData()
					if not len(self.coorTxt):
						index = np.searchsorted(data[0], mousePoint.x())
						if 0 < index and index < len(data[0]):
							self.coorTxt = "x = " + str(data[0][index])
					if 0 < index and index < len(data[0]):
						self.coorTxt += (', <span style="color:{:s}">y({:s})'
							'= {:.3e}</span>').format(self.colors[k], t.name(),
										data[1][index])
				self.status.setText(self.coorTxt)
			self.vLine.setPos(mousePoint.x())
			self.hLine.setPos(mousePoint.y())
		self.update()
	
	def event(self, evt):
		'''
		Override event() function to catch window active event. Send focusInSig 
		for main window to be set as active window for appending plots.
		'''
		if evt.type() == QEvent.WindowActivate:
			self.focusInSig.emit()
		return super().event(evt)

	def closeEvent(self, event):
		'''
		When close, send closeSig for main window to remove it from window list.
		'''
		self.closeSig.emit()
		super().closeEvent(event)

class SimplePlotWindow(QDialog):
	'''
	To contain pyqtgraph.PlotWidget and this window could be closed.
	'''
	def __init__(self, parent = None):
		super().__init__(parent)
		self.widgets = {}
		'''
		plotW = pg.PlotWidget(self, background = 'w')
		self.topGrid = QGridLayout(self)
		self.topGrid.addWidget(plotW, 0, 0)
		self.widgets[(0, 0)] = plotW
		self.plotI = plotW.getPlotItem()
		'''
		topVB = QVBoxLayout(self)
		self.GL = pg.GraphicsLayoutWidget(self)
		self.GL.setBackground('w')
		self.plotI = self.GL.addPlot()
		self.widgets[(0, 0)] = self.plotI
		topVB.addWidget(self.GL)

		self.setAttribute(Qt.WA_DeleteOnClose)
		self.show()
	
	def plot(self, *args, **kwargs):
		self.plotI.clear()
		self.plotI.plot(*args, **kwargs)
	
	def showPlot(self, params, pos):
		'''
		Replace content in current plotItem.

		Parameters
		----------
		params: list
			List of parameter dictionaries for plot.plot_trace.
		pos: tuple
			Row and column position to place the plot.
		'''
		if pos in self.widgets:
			self.plotI = self.widgets[pos]
		else:
			self.plotI = self.GL.addPlot(*pos)
			self.widgets[pos] = self.plotI

		self.plotI.clear()
		for k in params:
			plot.plot_trace(ax = self.plotI, **k)
	
	def linkPlot(self, pos1, pos2):
		'''
		Link scaling of two plots in the plot window.

		Parameters
		----------
		pos1: tuple
			Row and column position of the first plot.
		pos2: tuple
			Row and column position of the second plot.
		'''
		if pos1 in self.widgets and pos2 in self.widgets:
			pltW1 = self.widgets[pos1]
			pltW2 = self.widgets[pos2]
			pltW1.setXLink(pltW2)
			pltW1.setYLink(pltW2)
	
	def clear(self):
		'''
		Remove everything that's plotted.
		'''
		for k, v in self.widgets.items():
			self.widgets[k] = None
			# self.topGrid.removeWidget(v)
			self.GL.removeItem(v)
			del(v)
		self.widgets.clear()
		'''
		plotW = pg.PlotWidget(self, background = 'w')
		self.topGrid.addWidget(plotW, 0, 0)
		self.widgets[(0, 0)] = plotW
		self.plotI = plotW.getPlotItem()
		'''
		self.plotI = self.GL.addPlot(0, 0)
		self.widgets[(0, 0)] = self.plotI
