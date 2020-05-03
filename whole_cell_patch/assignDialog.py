# Dialog with a table widget to assign cell type or trial protocol.

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, \
		QDialog, QTableWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout
import numpy as np
import pandas as pd
from .cpTableWidget import CpTableWidget

class AssignDialog(QDialog):
	'''
	Dialog with a table widget to assign cell type or trial protocol.
	'''
	assigned = pyqtSignal(pd.DataFrame)

	def __init__(self, inDF, parent = None):
		'''
		Build window based on input table.

		Parameters
		----------
		inDF: pandas.DataFrame
			Input table specifying table structure and index values

		Attributes
		----------
		df: pandas.DataFrame
			Used to keep track of the data input for return.
		dfTb: CpTableWidget
			Table widget used for input types or protocols.
		'''
		super().__init__(parent)
		self.df = inDF
		nrows = inDF.shape[0] + inDF.columns.nlevels
		ncols = inDF.shape[1] + inDF.index.nlevels
		self.dfTb = CpTableWidget(nrows, ncols, self)
		if inDF.index.nlevels > 1:
			for i, name in enumerate(inDF.index.names):
				it = QTableWidgetItem(name)
				it.setFlags(Qt.ItemIsEnabled)
				self.dfTb.setItem(inDF.columns.nlevels - 1, i, it)
				for j, num in enumerate(inDF.index.levels[i]):
					it = QTableWidgetItem(str(num))
					it.setFlags(Qt.ItemIsEnabled)
					self.dfTb.setItem(inDF.columns.nlevels + j, i, it)
		else:
			it = QTableWidgetItem(inDF.index.name)
			it.setFlags(Qt.ItemIsEnabled)
			self.dfTb.setItem(inDF.columns.nlevels - 1, 0, it)
			for j, num in enumerate(inDF.index):
				it = QTableWidgetItem(str(num))
				it.setFlags(Qt.ItemIsEnabled)
				self.dfTb.setItem(inDF.columns.nlevels + j, 0, it)
		if inDF.columns.nlevels > 1:
			for i, names in enumerate(inDF.columns.levels):
				for j, name in enumerate(names):
					it = QTableWidgetItem(name)
					it.setFlags(Qt.ItemIsEnabled)
					self.dfTb.setItem(i, inDF.index.nlevels + j, it)
		else:
			for j, name in enumerate(inDF.columns):
				it = QTableWidgetItem(name)
				it.setFlags(Qt.ItemIsEnabled)
				self.dfTb.setItem(0, inDF.index.nlevels + j, it)
		for i in range(len(inDF.index)):
			for j in range(len(inDF.columns)):
				it = QTableWidgetItem(str(inDF.iloc[i, j]))
				self.dfTb.setItem(i + inDF.columns.nlevels,
						j + inDF.index.nlevels, it)
		self.acceptBtn = QPushButton("OK", self)
		self.cancelBtn = QPushButton("Cancel", self)
		btnHB = QHBoxLayout()
		btnHB.addWidget(self.acceptBtn)
		btnHB.addWidget(self.cancelBtn)
		topVB = QVBoxLayout(self)
		topVB.addWidget(self.dfTb)
		topVB.addLayout(btnHB)
		self.acceptBtn.clicked.connect(self.finish)
		self.cancelBtn.clicked.connect(lambda: self.done(QDialog.Rejected))
		self.show()
	
	def start(self):
		'''
		Start this dialog to get input.
		'''
		self.open()
	
	def finish(self):
		'''
		When inputs confirmed, stop and emit signal with the table of 
		inputs

		Signal
		------
		assigned: 
			Signal of confirming assignment and returns table.
		'''
		for i in range(self.df.shape[0]):
			for j in range(self.df.shape[1]):
				it = self.dfTb.item(self.df.columns.nlevels + i, 
						self.df.index.nlevels + j)
				if it == None:
					self.df.iloc[i, j] = ''
				else:
					self.df.iloc[i, j] = it.text()
		self.assigned.emit(self.df)
		# self.assigned.disconnect()
		self.done(QDialog.Accepted)
