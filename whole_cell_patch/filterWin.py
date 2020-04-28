# Dialog managing filters and their parameters.

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QLineEdit, QVBoxLayout, QHBoxLayout, QDialog, QListWidget
from .filterDialog import FilterDialog, FilterParamDialog
	
class FilterWin(QDialog):
	'''
	Dialog  managing filters and their parameters.
	'''
	filterApplied = pyqtSignal(list)
	itFont = QFont()
	itFont.setItalic(True)

	def __init__(self, default, name = "Filters", parent = None):
		'''
		Build the window. initializing the filter related attributes.

		Parameters
		----------
		default: list
			List of filters, which are dictionaries with names under
			key "name" and parameter elements. Parameters are in string 
			format.
		name: list, optional
			Name of this window, default is Filters.
		parant: QWidget, optional
			Parent widgets, default is None.

		Attributes
		----------
		defaultFilters: list
			List of available filters and their default parameters. 
		filters: list
			List of filters to be applied.
		enabled: list
			List of 0 and 1 masking disabled filters.
		filterDialog: FilterDialog object
			Used to select filters.
		filterParamDialog: FilterParamDialog object
			Used to set filter parameters.
		'''
		super().__init__(parent)
		self.defaultFilters = default
		self.filters = []
		self.enabled = []
		self.filterDialog = FilterDialog(default, self)
		self.filterParamDialog = FilterParamDialog(self)
		self.filterLw = QListWidget(self)
		self.paramLb = QLabel('') 
		addBtn = QPushButton("Add")
		removeBtn = QPushButton("Remove")
		editBtn = QPushButton("Edit")
		enableBtn = QPushButton("Enable")
		disableBtn = QPushButton("Disable")
		applyBtn = QPushButton("Apply")
		topVB = QVBoxLayout(self)
		topVB.addWidget(self.filterLw)
		topVB.addWidget(self.paramLb)
		btnGrid = QGridLayout()
		btnGrid.addWidget(addBtn, 0, 0)
		btnGrid.addWidget(removeBtn, 0, 1)
		btnGrid.addWidget(editBtn, 0, 2)
		btnGrid.addWidget(enableBtn, 1, 0)
		btnGrid.addWidget(disableBtn, 1, 1)
		btnGrid.addWidget(applyBtn, 1, 2)
		topVB.addLayout(btnGrid)
		# self.filterLw.currentRowChanged.connect(self.showParam)
		self.filterLw.itemClicked.connect(self.showParam)
		addBtn.clicked.connect(self.addFilter)
		removeBtn.clicked.connect(self.removeFilter)
		editBtn.clicked.connect(self.editFilter)
		enableBtn.clicked.connect(self.enableFilter)
		disableBtn.clicked.connect(self.disableFilter)
		applyBtn.clicked.connect(self.applyFilters)
	
	def showParam(self, item):
		'''
		Display parameters of currently selected filter.

		Parameters
		----------
		item: QListWidgetItem
			Current filter item.
		'''
		num = self.filterLw.row(item)
		if num != -1:
			paramStr = ', '.join([k + ':' + v for k, v in 
				self.filters[num].items() if k != "name"])
			self.paramLb.setText(paramStr)
	
	def editParam(self, num = -1, adding = True):
		'''
		Pop up a dialog for choosing filter and setting parameters.

		Parameters
		----------
		num: int, optional
			Id of the filter to be based on.
		adding: bool, optional
			Whether to edit for adding filter (True, edit based on parameters 
			from default filters) or changing current filters (False). Default 
			is adding.
		'''
		if -1 < num:
			if adding:
				filt = self.defaultFilters[num]
			else:
				filt = self.filters[num]
			self.filterParamDialog.makeForm(filt)
			ret = self.filterParamDialog.exec_()
			if ret == QDialog.Accepted:
				retFilt = self.filterParamDialog.getForm()
				retFilt["name"] = filt["name"]
				if adding:
					self.filters.append(retFilt)
					self.enabled.append(1)
				else:
					self.filters[num] = retFilt
					del filt
				return 1
		return 0
	
	def addFilter(self, _):
		'''
		Add filter.
		'''
		ret = self.filterDialog.exec_()
		if -1 < ret:
			pret = self.editParam(ret) 
			if pret == 1:
				self.filterLw.addItem(self.defaultFilters[ret]["name"])
	
	def removeFilter(self, _):
		'''
		Remove filter.
		'''
		num = self.filterLw.currentRow()
		if num > -1:
			self.filters.pop(num)
			self.enabled.pop(num)
			self.filterLw.takeItem(num)
			self.filterLw.update()
	
	def editFilter(self, _):
		'''
		Edit filter.
		'''
		num = self.filterLw.currentRow()
		self.editParam(num, False)
		self.paramLb.update()
	
	def enableFilter(self, _):
		'''
		Enable selected filter.
		'''
		num = self.filterLw.currentRow()
		if -1 < num:
			self.enabled[num] = 1
			self.filterLw.item(num).setFont(QFont())

	def disableFilter(self, _):
		'''
		Disable selected filter.
		'''
		num = self.filterLw.currentRow()
		if -1 < num:
			self.enabled[num] = 0
			self.filterLw.item(num).setFont(self.itFont)
	
	def applyFilters(self, _):
		'''
		Emit signal to apply changes to filters.
		'''
		self.filterApplied.emit([f for f, n in 
			zip(self.filters, self.enabled) if n])
		self.paramLb.setText("Applied")
		self.paramLb.update()
