# Dialog window used to set basic parameters for a analysis method.

from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QVBoxLayout, QHBoxLayout, QDialog, QMessageBox
from .paramWidget import ParamWidget

class ParamDialog(QDialog):
	'''
	Dialog window used to set basic parameters for a analysis method.
	'''
	def __init__(self, paramTyp, param, parent = None):
		'''
		Build the window.
		'''
		super().__init__(parent)
		self.setModal(True)
		self.paramGrid = ParamWidget(paramTyp, param)
		okBtn = QPushButton("OK")
		cancelBtn = QPushButton("Cancel")
		topVB = QVBoxLayout(self)
		topVB.addLayout(self.paramGrid)
		topVB.addWidget(okBtn)
		topVB.addWidget(cancelBtn)
		okBtn.clicked.connect(self.accept)
		cancelBtn.clicked.connect(self.reject)
	
	def getParam(self):
		'''
		Return parameters from this window.
		'''
		return self.paramGrid.getParam()

	def updateDisp(self, param):
		'''
		After parameter changes due to importing or change of protocols,
		update display of parameters.

		Parameters
		----------
		param: dictionary
			New parameters. Default is None, only tend to update protocols.
		'''
		self.paramGrid.updateDisp(param)
		self.update()
