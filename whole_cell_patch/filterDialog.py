# Dialogs for setting filter parameters.

from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QLineEdit, QVBoxLayout, QHBoxLayout, QDialog, QComboBox, QWidget
from PyQt5.QtCore import pyqtSignal

class FilterDialog(QDialog):
	'''
	Dialog for choosing filter types.
	'''
	def __init__(self, default, parent = None):
		'''
		Build ui and set up parameter setting 

		Parameters
		----------
		default: list
			List of filters, which are dictionaries with names under
			key "name" and parameter elements.
		parent: QWidget, optional
			Parent widget.

		Attributes
		----------
		fnames: dictionary
			Names of filters, two nested dictionaries to specify two
			properties about the type of filters.
		'''
		self.defaultFilters = default
		super().__init__(parent)
		self.filterCb = QComboBox(self)  # Filter type
		self.bandCb = QComboBox(self)  # Band type
		self.fnames = {}
		count = 0
		for f in default:
			names = f["name"].split(',')
			if names[0] not in self.fnames:
				self.fnames[names[0]] = {}
				self.filterCb.addItem(names[0])
			if len(names) > 1:
				if names[1] not in self.fnames[names[0]]:
					self.fnames[names[0]][names[1]] = count
			else:
				self.fnames[names[0]][''] = count
			count += 1
		okBtn = QPushButton("OK", self)
		cancelBtn = QPushButton("Cancel", self)
		okBtn.clicked.connect(self.accept)
		cancelBtn.clicked.connect(self.reject)
		self.filterCb.currentTextChanged.connect(self.updateBand)
		topVB = QVBoxLayout(self)
		topVB.addWidget(self.filterCb)
		topVB.addWidget(self.bandCb)
		topVB.addWidget(okBtn)
		topVB.addWidget(cancelBtn)
	
	def updateBand(self, name):
		'''
		Update list of band in the band combobox.

		Parameters
		----------
		name: str
			Name of filter type.
		'''
		self.bandCb.clear()
		self.bandCb.addItems(list(self.fnames[name].keys()))

	def exec_(self):
		'''
		Override QDialog exec_ function. Alter return code to -1 for rejection
		and integer number for chosen filter's id.
		'''
		ret = super().exec_()
		if ret:
			return self.fnames[self.filterCb.currentText()][
					self.bandCb.currentText()]
		else:
			return -1
		

class FilterParamDialog(QDialog):
	'''
	Dialog for setting filter parameters.
	'''
	def __init__(self, parent = None):
		'''
		Build ui and set up connections.

		Parameters
		----------
		parent: QWidget, optional
			Parent widget.

		Attributes
		----------
		form: dictionary
			Parameter names as keys and corresponding QLineEdit object
			as values.
		formWd: QWidget
			Container for displaying the parameter setting form.
		'''
		super().__init__(parent)
		self.form = {}
		okBtn = QPushButton("OK", self)
		cancelBtn = QPushButton("Cancel", self)
		topVB = QVBoxLayout(self)
		self.formVB = QVBoxLayout()
		self.formWd = None
		btnHB = QHBoxLayout()
		btnHB.addWidget(okBtn)
		btnHB.addWidget(cancelBtn)
		cancelBtn.clicked.connect(self.reject)
		okBtn.clicked.connect(self.accept)
		topVB.addLayout(self.formVB)
		topVB.addLayout(btnHB)
	
	def makeForm(self, filt):
		'''
		Build parameters setting grid layout for filter filt.

		Parameters
		----------
		filt: dictionary
			Filter information, parameters are in string format.
		'''
		# clear the previous form widget
		if self.formWd != None:
			self.formVB.removeWidget(self.formWd)
			self.form = {}
			self.formWd.setParent(None)
			del self.formWd  
			self.formWd = None
		self.formWd = QWidget()
		formGrid = QGridLayout(self.formWd)
		row = 0
		for k, v in filt.items():
			if k != "name":
				self.form[k] = QLineEdit(v, self.formWd)
				formGrid.addWidget(QLabel(k, self.formWd), row, 0)
				formGrid.addWidget(self.form[k], row, 1)
				row = row + 1
		self.formVB.addWidget(self.formWd)
	
	def getForm(self):
		'''
		Get the parameters filled in the QLineEdit objects.

		Returns
		-------
		filt: dictionary
			Filter information, without name.
		'''
		filt = {}
		for k, v in self.form.items():
			filt[k] = v.text()
		return filt
