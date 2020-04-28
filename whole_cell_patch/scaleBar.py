# Modified ScaleBar from pyqtgraph able to show y axis scale and 
# to be dragged around.

from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph import GraphicsObject
# from pyqtgraph import GraphicsWidget
from pyqtgraph import GraphicsWidgetAnchor
from pyqtgraph import Point
'''
from .TextItem import TextItem
import numpy as np
from .. import functions as fn
from .. import getConfigOption
from ..Point import Point
'''

class ScaleBar(GraphicsObject, GraphicsWidgetAnchor):
	'''
	A scale bar indicating specified length x and y axis.

	Note that this item could be initialized with a PlotItem as parent.
	'''
	def __init__(self, x = 1, y = 1, parent = None, barWidth = 3, 
			brush = None, offset = None):
		'''
		Initialze the geometry parameters for the bars.

		Paramters
		---------
		x: float, optional
			Horizontal bar length. Default is 1 unit on x axis.
		y: float, optional
			Vertical bar length. Default is 1 unit on y axis.
		parent: pyqtgraph.plotItem, optional
			QGraphicsWidget containing these scale bars.
		barWidth: float, optional
			Width of the scale bars. Default is 3 pixels.
		brush: QBrush, optional
			Brush for the bars.
		offset: float, optional
			Specifies the offset position relative to the bars' parent.
			Positive values offset from the left or top; negative values
			offset from the right or bottom. Default is None, will be 
			put somewhere in the corner, could be moved by mouse dragging.
		'''
		GraphicsObject.__init__(self)
		GraphicsWidgetAnchor.__init__(self)
		self.setFlag(self.ItemHasNoContents)
		self.offset = offset
		# if offset == None:
		self.setFlag(self.ItemIgnoresTransformations)
		self.xs, self.ys = x, y
		self.xlen = 0
		self.ylen = 0
		self.xbar = QtGui.QGraphicsRectItem(self)
		self.ybar = QtGui.QGraphicsRectItem(self)
		if brush is None:
			brush = pg.getConfigOption("foreground")
		self.xbar.setBrush(brush)
		self.ybar.setBrush(brush)
		self.barWidth = barWidth
		self.setParentItem(parent)
	
	def boundingRect(self):
		return QtCore.QRectF(0, 0, self.xlen, self.ylen)
	
	def updateBar(self):
		'''
		Update bar lengths when parent is scaled.
		'''
		view = self.parentItem()
		p1 = view.mapFromView(QtCore.QPointF(0,0))
		p2 = view.mapFromView(QtCore.QPointF(self.xs, self.ys))
		self.prepareGeometryChange()
		self.xlen = (p2-p1).x()
		self.ylen = -(p2-p1).y()
		self.xbar.setRect(QtCore.QRectF(0, self.ylen - self.barWidth, 
			self.xlen, self.barWidth))
		self.ybar.setRect(QtCore.QRectF(0, 0, self.barWidth, self.ylen))
		
	def setParentItem(self, p):
		print(p)
		ret = GraphicsObject.setParentItem(self, p)
		if self.offset is not None:
			offset = Point(self.offset)
			anchorx = 1 if offset[0] <= 0 else 0
			anchory = 1 if offset[1] <= 0 else 0
			anchor = (anchorx, anchory)
			self.anchor(itemPos=anchor, parentPos=anchor, offset=offset)
		return ret
	
	def parentChanged(self):
		view = self.parentItem()
		print(view)
		if view is None:
			return
		view.sigRangeChanged.connect(self.updateBar)
		self.updateBar()

	def hoverEvent(self, ev):
		ev.acceptDrags(QtCore.Qt.LeftButton)
		
	def mouseDragEvent(self, ev):
		if ev.button() == QtCore.Qt.LeftButton:
			dpos = ev.pos() - ev.lastPos()
			self.autoAnchor(self.pos() + dpos)
