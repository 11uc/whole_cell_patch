# The input to set parameters.

from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QTextEdit, QDialog
import numpy as np
import pandas as pd
from .param import ParamMan

class SetParamWin(QDialog):
	'''
	A dialog used to input multiple numerical parameters.
	'''
	def __init__(self, params, parent = None):
		'''
		Build the window based on the parameter dictionary provided.

		Parameters
		----------
		params: dictionary
			Dictionary of parameters with key as names.
		'''
		self.ori = params
		super().__init__(parent)
		paramGrid = QGridLayout(self)
		i = 0
		tes = []
		for k in params:
			paramGrid.addWidget(QLabel(k), i, 0)
			te = QTextEdit(QString.number(params[k]))
			paramGrid.addWidget(te, i, 1)
			tes.append(te)
			i += 1
		acceptBtn = QPushButton("OK")
		rejectBtn = QPushButton("Cancel")
		paramGrid.addWidget(acceptBtn, i, 0)
		paramGrid.addWidget(rejectBtn, i, 1)
		self.setLayout(QGridLayout)
		self.show()
	
	def readParams(self):
		'''
		Read parameters from the text inputs
		'''
		pc = {}
		i = 0
		for k in self.ori:
			pc[k] = type(self.ori[k])(tes[i].toPlainText())
		return pc

	@staticmethod
	def setParams(params):
		'''
		Static method used to build window and set parameters.
		'''
		w = SetParamWin(params)
		ret = w.exc_()
		if ret:
			return w.readParams()
		else:
			return None
