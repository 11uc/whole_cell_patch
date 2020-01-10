# Build windows for analyze modules.

from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, QEvent
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QLineEdit, QVBoxLayout, QHBoxLayout, QApplication, QDialog, \
		QComboBox, QMessageBox, QWidget
import numpy as np
import pandas as pd
from .param import ParamMan
from .paramWidget import ParamWidget
from .paramDialog import ParamDialog

class AnalyzeModuleWindow(QDialog):
	'''
	Window used for doing analysis, containing buttons and text boxes
	to set parameters and buttons to start analysis.
	'''
	def __init__(self, name, module, paramMan, projMan, parent = None):
		'''
		Window to run the module.

		Parameters
		----------
		busy: bool
			Whether an analysis is running.
		name: string
			Name of this module, will be shown in the menu.
		module: object
			Module class instance use to do the analysis.
		paramMan: ParamMan
			Parameter management class, used for analysis and display.
		projMan: Project
			Project management class, used for access raw data.
		parent: object, optional
			Parent window.
		'''
		super().__init__(parent)
		self.busy = False
		self.setWindowTitle(name)
		self.paramMan = paramMan
		self.name = name
		self.module = module
		paramSetBtn = QPushButton("Parameters")
		topVB = QVBoxLayout(self)
		self.ctlWd = QWidget()
		ctlVB = QVBoxLayout(self.ctlWd)
		ctlVB.addWidget(paramSetBtn)
		self.basic, self.profiles = module.profile()
		self.paramDg = ParamDialog(self.basic, paramMan.get(
			"basic_" + name, module.loadDefault("basic")), parent = self)
		paramSetBtn.clicked.connect(self.paramDg.show)
		self.paramDg.accepted.connect(self.changeBasic)
		self.paramGrids = []
		self.workerThreads = []
		for i, profile in enumerate(self.profiles):
			wth = Worker(self, i)
			self.workerThreads.append(wth)
			paramGrid = ParamWidget(profile["param"], 
					paramMan.get(profile["pname"],
						module.loadDefault(profile["pname"])), projMan)
			self.paramGrids.append(paramGrid)
			methodBtn = QPushButton(profile["name"])
			wth.jobDone.connect(self.unlock)
			methodBtn.clicked.connect(wth.start)
			methodBtn.clicked.connect(self.lock)
			ctlVB.addLayout(paramGrid)
			ctlVB.addWidget(methodBtn)
		topVB.addWidget(self.ctlWd)
		stopBtn = QPushButton("Abort")
		stopBtn.clicked.connect(self.abort)
		topVB.addWidget(stopBtn)
		self.show()
	
	def __del__(self):
		'''
		Deal with worker thread.
		'''
		for w in self.workerThreads:
			w.quit()
			w.wait()

	def updateDisp(self, upParam = True):
		'''
		After parameter changes due to importing or change of protocols,
		update display of parameters.

		Parameters
		----------
		upParam: bool
			Whether to update parameters too. Default is true.
		'''
		if upParam:
			for pg, profile in zip(self.paramGrids, self.profiles):
				pg.updateDisp(self.paramMan.get(profile["pname"], 
					self.module.loadDefault(profile["pname"])))
			self.paramDg.updateDisp(self.paramMan.get("basic_" + self.name, 
				self.module.loadDefault("basic")))
			self.module.setBasic(self.paramMan.get("basic_" + self.name, 
				self.module.loadDefault("basic")))
		else:
			for pg in self.paramGrids:
				pg.updateDisp()
		self.update()

	def changeParams(self, n = -1):
		'''
		Actually change parameters in paramMan for parameters in set n.

		Parameters
		----------
		n: int, optional
			Default is -1, then change every set.

		Returns
		-------
		result: int
			0 for fail, 1 for sucess.
		'''
		if n == -1:
			for i in range(len(self.profiles)):
				p = self.paramGrids[i].getParam()
				if p == None:
					return 0
				self.paramMan.set(self.profiles[i]["pname"], p)
		else:
			p = self.paramGrids[n].getParam()
			if p == None:
				return 0
			self.paramMan.set(self.profiles[n]["pname"], p)
		return 1

	def changeBasic(self):
		'''
		Change basic parameters in paramMan.
		Returns
		-------
		result: int
			0 for fail, 1 for sucess.
		'''
		p = self.paramDg.getParam()
		if p == None:
			QMessageBox.warning(self, "Warning", "Wrong parameter format",
					QMessageBox.Ok)
			return 0
		else:
			self.paramMan.set("basic_" + self.name, p)
			self.module.setBasic(p)
			return 1
	
	def lock(self):
		'''
		Inactivate current analysis window while analysis is running.
		Also set attibutes to indicate analysis running to block
		changes that could happen in main window.
		'''
		self.ctlWd.setEnabled(False)
		self.busy = True
		self.update()
	
	def unlock(self, good):
		'''
		Unlock after analysis finished.
		'''
		self.ctlWd.setEnabled(True)
		self.busy = False
		if not good:
			QMessageBox.warning(self, "Warning", 
					"Wrong parameter format",
					QMessageBox.Ok)
	
	def abort(self):
		'''
		Stop running analysis.
		'''
		if self.busy:
			self.module.stop()

	
class Worker(QThread):
	'''
	Worker thread object to run the analysis function in a separate thread.
	'''
	# Job done good or not.
	jobDone = pyqtSignal(bool)

	def __init__(self, controller, idx):
		'''
		Initilize parameters needed for the function.

		Parameters
		----------
		controller: AnalyzeModuleWindow
			Information about the function comes from the controller.
		idx: int
			Worker id, used to determine which function to run.
		'''
		super().__init__()
		self.controller = controller
		self.idx = idx
		self.pn = controller.profiles[idx]["pname"]
		self.foo = controller.profiles[idx]["foo"]
	
	@pyqtSlot()
	def run(self):
		'''
		Run the function after updating the parameter. Also need to show 
		warning message if things went wrong.
		'''
		ret = self.controller.changeParams(self.idx)
		if ret:
			self.foo(**self.controller.paramMan.get(self.pn))
			self.jobDone.emit(True)
		else:
			self.jobDone.emit(False)
