# Dialog used to select cells for assigning protocols or types

import bisect
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QTextEdit, QDialog, QListWidget, QListWidgetItem, QVBoxLayout, \
		QHBoxLayout

class SelectCellDialog(QDialog):
	'''
	Dialog used to select cells or trials for assigning protocols or types.
	'''
	selected = pyqtSignal(tuple)

	def __init__(self, parent = None):
		'''
		Initialize and build the window.

		Parameters
		----------
		parent: QWidget
			Parent window.

		Attributes
		----------
		items: list of QListWidgetItem
			Items to display in QListWidget.
		included: list of int
			Included cell numbers.
		excluded: list of int
			Excluded cell numbers.
		'''
		super().__init__(parent)
		self.incLW = QListWidget(self)
		self.excLW = QListWidget(self)
		self.incLb = QLabel("Included")
		self.excLb = QLabel("Excluded")
		incVB = QVBoxLayout()
		excVB = QVBoxLayout()
		incVB.addWidget(self.incLb)
		incVB.addWidget(self.incLW)
		excVB.addWidget(self.excLb)
		excVB.addWidget(self.excLW)
		excAllBtn = QPushButton(">>", self)
		excBtn = QPushButton('>', self)
		incBtn = QPushButton('<', self)
		incAllBtn = QPushButton("<<", self)
		btnVB = QVBoxLayout()
		btnVB.addWidget(excAllBtn)
		btnVB.addWidget(excBtn)
		btnVB.addWidget(incBtn)
		btnVB.addWidget(incAllBtn)
		selectHB = QHBoxLayout()
		selectHB.addLayout(incVB)
		selectHB.addLayout(btnVB)
		selectHB.addLayout(excVB)
		acceptBtn = QPushButton("OK", self)
		acceptBtn.setDefault(True)
		cancelBtn = QPushButton("Cancel", self)
		btnHB = QHBoxLayout()
		btnHB.addWidget(acceptBtn)
		btnHB.addWidget(cancelBtn)
		topVB = QVBoxLayout(self)
		topVB.addLayout(selectHB)
		topVB.addLayout(btnHB)
		self.items = []
		self.included = []
		self.excluded = []
		# key binding
		incAllBtn.clicked.connect(self.includeAll)
		excAllBtn.clicked.connect(self.excludeAll)
		incBtn.clicked.connect(self.include)
		excBtn.clicked.connect(self.exclude)
		acceptBtn.clicked.connect(self.finish)
		cancelBtn.clicked.connect(self.reject)
	
	def start(self, inc, exc):
		'''
		Overload dialog open function, initializing items before
		showing the dialog.

		Parameters
		----------
		inc: list of int
			Predefined included cell numbers.
		exc: list of int
			Predefined excluded cell numbers.
		'''
		self.included = sorted(inc)
		self.excluded = sorted(exc)
		self.incLW.clear()
		self.excLW.clear()
		self.items = [None] * (max(self.included + self.excluded))
		for c in self.included:
			self.items[c - 1] = QListWidgetItem(str(c))
			self.incLW.addItem(self.items[c - 1])
		for c in self.excluded:
			self.items[c - 1] = QListWidgetItem(str(c))
			self.excLW.addItem(self.items[c - 1])
		super().open()
	
	def finish(self):
		'''
		Finish selection, raise selectd signal with (inc, exc) as parameter.

		Signals
		-------
		selected: 
			Signalling selection is finished and return selection results.
		'''
		self.accept()
		self.selected.emit((self.included, self.excluded))

	def include(self):
		'''
		Move the selected items from excluded list to included list.
		'''
		for item in self.excLW.selectedItems():
			c = int(item.text())
			i = bisect.bisect_left(self.excluded, c)
			self.excLW.takeItem(i)
			self.excluded.pop(i)
			j = bisect.bisect_left(self.included, c)
			self.included.insert(j, c)
			self.incLW.insertItem(j, item)
		self.incLW.update()
		self.excLW.update()

	def exclude(self):
		'''
		Move the selected items from included list to excluded list.
		'''
		for item in self.incLW.selectedItems():
			c = int(item.text())
			i = bisect.bisect_left(self.included, c)
			self.incLW.takeItem(i)
			self.included.pop(i)
			j = bisect.bisect_left(self.excluded, c)
			self.excluded.insert(j, c)
			self.excLW.insertItem(j, item)
		self.incLW.update()
		self.excLW.update()
	
	def includeAll(self):
		'''
		Move all items from excluded list ot included list.
		'''
		while len(self.excluded):
			item = self.excLW.takeItem(0)
			c = self.excluded.pop(0)
			j = bisect.bisect_left(self.included, c)
			self.included.insert(j, c)
			self.incLW.insertItem(j, item)
		self.excLW.update()
		self.incLW.update()

	def excludeAll(self):
		'''
		Move all items from included list ot excluded list.
		'''
		while len(self.included):
			item = self.incLW.takeItem(0)
			c = self.included.pop(0)
			j = bisect.bisect_left(self.excluded, c)
			self.excluded.insert(j, c)
			self.excLW.insertItem(j, item)
		self.incLW.update()
		self.excLW.update()
	
	def changeTarget(self, target):
		'''
		Change display included or excluded subject.
		'''
		self.incLb.setText("Included " + target)
		self.excLb.setText("Excluded " + target)
