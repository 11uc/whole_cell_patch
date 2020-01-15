# Abstract base class defining common methods for analysis classes.

import copy
import pyqtgraph as pg
from PyQt5.QtCore import QEventLoop, pyqtSignal, QObject, QMutex

class Analysis(QObject):
	'''
	Base analysis class defining methods required to provided information
	for the gui and methods used for output to the gui.
	'''
	textOut = pyqtSignal(str)
	plotOut = pyqtSignal(dict)
	plotLink = pyqtSignal(list)
	plotClear = pyqtSignal()

	def __init__(self, inTxtWidget):
		'''
		Define attributes.

		Attributes
		----------
		inTxtWidget: QLineEdit
			Input line widget of the main window.
		'''
		super().__init__()
		self.itw = inTxtWidget
		self.toStop = False
		self.qm = QMutex()

	def loadDefault(self, name):
		'''
		Define default parameters used by this analysis and return them
		by name, used when parameters are not specified or as template 
		for specifying them.
		'''
		raise NotImplementedError(("Default parameters need to be defined."))

	def setBasic(self, param):
		'''
		Change basic parameters separately.
		'''
		raise NotImplementedError(("Basic parameter setting missing."))
	
	
	def profile(self):
		'''
		Return the profile of this module so that the gui could display
		the parameters and the functions.

		Returns
		-------
		basicParam: dictionary
			Format of basic parameters. Keys are the same as in basic parameters
			and values describe the type of parameters.
			- "int" : integer
			- "float" : float
			- "protocol" : protocol, to be chosen from protocols of a project
			- "intr": range of integers, two integers specifying a range
			- "floatr": range of floats, two floats specifying a range
			- "intl": list of integers
			- "floatl: list of floats
			- "bool": boolean
			- "combo,option1,option2,...": choices among a few options,
				start with type work "combo", followed by option strings
				separated by comma.
		prof: list of dictionaries
			The profile for functions. Each dictionary describe one function.
			The key : value pairs are:
			- "name" : name of the function
			- "pname" : name of the parameter dictionary key
			- "foo" : the function that could be called
			- "param" : parameter types, same format as the basicParam
		'''
		raise NotImplementedError("Module profile needs to be defined.")

	def stopRequested(self):
		'''
		Check if stop of an analysis is requested by the user. Use this function
		in analysis methods, usually in a loop where it's safe to stop. If it's
		true, stop the analysis as requested. When stop is requested, update
		the flag to False.

		Returns
		-------
		ret: bool
			Requested or not.
		'''
		self.qm.lock()
		ret = copy.copy(self.toStop)
		if ret:
			self.toStop = False
		self.qm.unlock()
		return ret
	
	def stop(self):
		'''
		Request to stop any analysis process in this module.
		'''
		self.qm.lock()
		self.toStop = True
		self.qm.unlock()

	def prt(self, *args, sep = ' ', end = '\n'):
		'''
		Print text into the widget provided by the gui, used to 
		show analysis progress.

		Parameters
		----------
		*args:
			Strings to be printed.
		sep: str
			Separating string
		end: str
			Ending string, not used.
		'''
		self.textOut.emit(sep.join([d.__str__() for d in args]))
	
	def ipt(self, *args, sep = ' ', end = '\n'):
		'''
		Get text input from the gui, could be used for manual adjustment
		of the analysis.

		Parameters
		----------
		Same as prt. Input instruction text to be displayed.

		Returns
		-------
		text: string
			Input text
		'''
		self.textOut.emit(sep.join([d.__str__() for d in args]))
		loop = QEventLoop()
		self.itw.returnPressed.connect(loop.quit)
		loop.exec_()
		text = self.itw.text()
		self.itw.setText('')
		self.prt('>', text)
		return text
	
	def plt(self, plotItem, row = 0, col = 0):
		'''
		Emit signal with pyqtgraph.PlotItem to plot in gui.

		Parameters
		----------
		plotItem: pyqtgraph.PlotItem
			Pyqtgraph PlotItem class with plots that going to be shown.
		row: int, optional
			Row number of the axes to plot in the plot window, default is 0.
			If a plot exists in that position, it will be removed.
		col: int, optional
			Column number of the axes to plot in the plot window, default is 0.
			If a plot exists in that position, it will be removed.
		'''
		self.plotOut.emit({"item": plotItem, "pos": (row, col)})
	
	def linkPlt(self, row1, col1, row2, col2):
		'''
		Link scaling of two plots in the plot window, emit plotLink signal
		to plot window to do it.

		Parameters
		----------
		row1: int
			Row number of the first axes.
		col1: int
			Column number of the first axes.
		row2: int
			Row number of the second axes.
		col2: int
			Columns number of the second axes.
		'''
		self.plotLink.emit([(row1, col1), (row2, col2)])

	def clearPlt(self):
		'''
		Clear plots to make place for new ones.
		'''
		self.plotClear.emit()
