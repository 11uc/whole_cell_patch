# class derived from a GridLayout with a bunch of widgets

from PyQt5.QtWidgets import QLabel, QGridLayout, QLineEdit, \
		QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox
import numpy as np
import pandas as pd

class ParamWidget(QGridLayout):
	'''
	Collecting all the input boxes and labels to assign data.
	'''
	def __init__(self, paramTyp, param, projMan = None, parent = None):
		'''
		Build the boxes.
		
		Parameters
		----------
		paramTyp: dictionary
			Defining types of parameters in the set.
		param: dictionary
			The parameters in the set read from paramMan.
		projMan: Project
			Project management class, used for access raw data.

		Attributes
		----------
		param: dictionary
			Parameter set managed by this grid widget.
		err: bool
			Whether there's an error in the parameters.
		senderList: 
		'''
		super().__init__(parent)
		self.err = False
		self.param = param
		self.paramTyp = paramTyp
		self.projMan = projMan
		self.senderList = []
		for i, (k, v) in enumerate(paramTyp.items()):
			self.addWidget(QLabel(k), i, 0)
			val = self.param[k]
			if v == "protocol" and projMan != None:
				cb = QComboBox()
				cb.currentTextChanged.connect(lambda x, ind = k, typ = v: \
						self.updateParam(ind, typ, x))
				self.addWidget(cb, i, 1)
				self.senderList.append(cb)
			elif v == "int" or v == "float":
				le = QLineEdit()
				le.textEdited.connect(lambda x, ind = k, typ = v: 
						self.updateParam(ind, typ, x))
				self.addWidget(le, i, 1)
				self.senderList.append(le)
			elif v == "intr" or v == "floatr":
				le0 = QLineEdit()
				le1 = QLineEdit()
				le0.textEdited.connect(lambda x, ind = k, typ = v: \
						self.updateParam(ind, typ, x, begin = True))
				le1.textEdited.connect(lambda x, ind = k, typ = v:
						self.updateParam(ind, typ, x, begin = False))
				twoHB = QHBoxLayout()
				twoHB.addWidget(le0)
				twoHB.addWidget(QLabel("to"))
				twoHB.addWidget(le1)
				self.addLayout(twoHB, i, 1)
				self.senderList.append([le0, le1])
			elif v == "intl" or v == "floatl" or v == "strl":
				le = QLineEdit()
				le.textEdited.connect(lambda x, ind = k, typ = v: \
						self.updateParam(ind, typ, x))
				btn = QPushButton("...")
				lstHB = QHBoxLayout()
				lstHB.addWidget(le)
				lstHB.addWidget(btn)
				self.addLayout(lstHB, i, 1)
				self.senderList.append(le)
			elif v == "bool":
				cb = QCheckBox()
				cb.stateChanged.connect(lambda x, ind = k, typ = v: \
						self.updateParam(ind, typ, x))
				self.addWidget(cb, i, 1)
				self.senderList.append(cb)
			elif "combo" in v:
				options = v.split(',')[1:]
				cb = QComboBox()
				for j in options:
					cb.addItem(j)
				cb.currentTextChanged.connect(lambda x, ind = k, typ = v: \
						self.updateParam(ind, typ, x))
				cb.setCurrentIndex(0)
				self.addWidget(cb, i, 1)
				self.senderList.append(cb)
			else:
				print("Unknown parameter type.")
		self.updateDisp()
		self.updateDisp(param)
	
	def updateDisp(self, param = None):
		'''
		After parameter changes due to importing or change of protocols,
		update display of parameters.

		Parameters
		----------
		param: dictionary, optional
			New parameters. Default is None, only tend to update protocols.
		'''
		if param == None:
			for i, (k, v) in enumerate(self.paramTyp.items()):
				if v == "protocol" and self.projMan != None:
					cb = self.senderList[i]
					cb.clear()
					pt = self.projMan.getProtocols()
					for j in pt:
						cb.addItem(j)
					if len(pt):
						cb.setCurrentIndex(0)
					else:
						self.err = True
		else:
			self.param = param
			for i, (k, v) in enumerate(self.paramTyp.items()):
				val = param[k]
				if v == "protocol" and self.projMan != None:
					cb = self.senderList[i]
					cb.clear()
					pt = self.projMan.getProtocols()
					for j in pt:
						cb.addItem(j)
					if len(pt):
						cb.setCurrentIndex(0)
					else:
						self.err = True
				elif v == "int" or v == "float":
					if v == "int" or (1e-3 < abs(val) and abs(val) < 1e3):
						ds = str(val)
					else:
						ds = "{:.3e}".format(val)
					le = self.senderList[i]
					le.setText(ds)
				elif v == "intr" or v == "floatr":
					le0, le1 = self.senderList[i]
					if v == "intr" or (1e-3 < abs(val[0]) and abs(val[0]) < 1e3):
						ds = str(val[0])
					else:
						ds = "{:.3e}".format(val[0])
					le0.setText(ds)
					if v == "intr" or (1e-3 < abs(val[1]) and abs(val[1]) < 1e3):
						ds = str(val[1])
					else:
						ds = "{:.3e}".format(val[1])
					le1.setText(ds)
				elif v == "intl" or v == "floatl":
					if len(val):
						if v == "intl" or (1e-3 < min(map(abs, val)) and \
								max(map(abs, val)) < 1e3):
							ds = ", ".join(map(str, val))
						else:
							ds = ", ".join(["{:.3e}".format(d) for d in val])
					else:
						ds = ''
					le = self.senderList[i]
					le.setText(ds)
				elif v == "strl":
					if len(val):
						ds = ", ".join(val)
					else:
						ds = ''
					le = self.senderList[i]
					le.setText(ds)
				elif v == "bool":
					cb = self.senderList[i]
					cb.setChecked(val)
				elif "combo" in v:
					cb = self.senderList[i]
					cb.setCurrentText(val)
				else:
					print("Unknown parameter type")
					print(v, val)
		self.update()

	def updateParam(self, ind, typ, val, **kargs):
		'''
		Update individual parameters in profile using values get
		from input widgets.
		
		Parameters
		----------
		ind: string
			Key of the individual parameter to be set.
		typ: string
			Type of the individual parameter.
		val: string
			Text out of the input widget with the value.
		**kargs:
			Arguments come with some special types of parameters.
			- begin: bool
				Whether it's the first one of the two value range parameters.
		'''
		try:
			self.err = False
			self.sender().setStyleSheet("background:#FFFFFF;")
			if typ == "int":
				self.param[ind] = int(val)
			elif typ == "float":
				self.param[ind] = float(val)
			elif typ == "intr":
				if kargs["begin"]:
					self.param[ind][0] = int(val)
				else:
					self.param[ind][1] = int(val)
			elif typ == "floatr":
				if kargs["begin"]:
					self.param[ind][0] = float(val)
				else:
					self.param[ind][1] = float(val)
			elif typ == "intl":
				if len(val):
					self.param[ind] = list(map(int, val.split(',')))
				else:
					self.param[ind] = []
			elif typ == "floatl":
				if len(val):
					self.param[ind] = list(map(float, val.split(',')))
				else:
					self.param[ind] = []
			elif typ == "strl":
				if len(val):
					self.param[ind] = [d.strip() for d in val.split(',')]
				else:
					self.param[ind] = []
			elif typ == "protocol":
				self.param[ind] = val
			elif typ == "bool":
				self.param[ind] = bool(val)
			elif "combo" in typ:
				self.param[ind] = val
			else:
				print("Unknown parameter type")
		except ValueError:
			self.sender().setStyleSheet("background:#FF0000;")
			self.err = True
	
	def getParam(self):
		'''
		Get parameters managed in this widget.
		'''
		if not self.err:
			return self.param
		else:
			return None
