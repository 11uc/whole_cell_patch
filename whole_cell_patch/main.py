# Main window and functions of the ephys analysis program

import sys
from PyQt5.QtCore import Qt, pyqtSlot, QEvent
from PyQt5.QtWidgets import QMainWindow, QAction, QLabel, QGridLayout, \
		QPushButton, QButtonGroup, QCheckBox, QVBoxLayout, QHBoxLayout, \
		QTextEdit, QWidget, QFileDialog, QApplication, \
		QMessageBox, QLineEdit, QComboBox
import pickle
import numpy as np
import pandas as pd
from .ap import AP
from .sealTest import SealTest
from .mini import Mini
from .sub import Sub
from .analyzeModule import AnalyzeModuleWindow
from .project import Project
from .param import ParamMan
from .projectDialog import ProjectDialog
from .selectCellDialog import SelectCellDialog
from .assignDialog import AssignDialog
from .plotWindow import PlotWindow, SimplePlotWindow

class wcpMainWindow(QMainWindow):
	'''
	Main window and functions of whole cell patch clamp recording
	results analysis.
	'''
	def __init__(self):
		super().__init__()
		self.proj = Project()
		self.param = ParamMan()
		self.projDg = ProjectDialog(self)
		self.selectDg = SelectCellDialog(self)
		self.selectDg.accepted.connect(self.disconnectSelectDg)
		self.selectDg.rejected.connect(self.disconnectSelectDg)
		self.plotWindows = []
		self.analyzeWindows = {}
		self.initUI()
		self.modules = []  # list with all the modules
		self.addModule("Action potential", AP)
		self.addModule("Seal test", SealTest)
		self.addModule("Mini analysis", Mini)
		self.addModule("Subthreshold response analysis", Sub)
		self.show()
	
	def initUI(self):
		'''
		Build the UI, all analysis functions are in the menu and the
		main window has controls for browsing the traces.
		'''
		menubar = self.menuBar()
		menubar.setNativeMenuBar(False)
		fileMenu = menubar.addMenu("&File")
		self.analysisMenu = menubar.addMenu("&Analysis")

		projNewAct = QAction("New project", self)
		projLoadAct = QAction("Load project", self)
		projSaveAct = QAction("Save project", self)
		projSaveAsAct = QAction("Save project as", self)
		exitAct = QAction("Exit", self)
		exitAct.setShortcut("Ctrl + Q")
		paramImportAct = QAction("Import parameters", self)
		paramExportAct = QAction("Export parameters", self)
		
		fileMenu.addAction(projNewAct)
		fileMenu.addAction(projLoadAct)
		fileMenu.addAction(projSaveAct)
		fileMenu.addAction(projSaveAsAct)
		fileMenu.addAction(exitAct)
		self.analysisMenu.addAction(paramImportAct)
		self.analysisMenu.addAction(paramExportAct)
		self.analysisMenu.addSeparator()

		self.projNameLb = QLabel("Name:")
		self.workDirLb = QLabel("Working Directory:")
		self.baseFldLb = QLabel("Raw Data Folder:")
		self.formatLb = QLabel("Data file name format:")
		eles = (self.projNameLb, self.workDirLb, self.baseFldLb,
				self.formatLb)
		projDispGrid = QGridLayout()
		for i, ele in enumerate(eles):
			projDispGrid.addWidget(ele, i, 0)
		selectCellBtn = QPushButton("Cells")
		assignProtBtn = QPushButton("Protocols")
		assignTypBtn = QPushButton("Types")
		editProjBtn = QPushButton("Edit")
		editHB = QHBoxLayout()
		editHB.addWidget(selectCellBtn)
		editHB.addWidget(editProjBtn)
		editHB.addWidget(assignProtBtn)
		editHB.addWidget(assignTypBtn)
		projDispGrid.addLayout(editHB, len(eles), 0)

		self.cellCb = QComboBox(self)
		optionBg = QButtonGroup(self)
		optionBg.setExclusive(True)
		self.trialCb = QCheckBox("Trial")
		self.stimCb = QCheckBox("Stim")
		optionBg.addButton(self.trialCb)
		optionBg.addButton(self.stimCb)
		self.trialCb.setCheckState(Qt.Checked)
		self.trialCbb = QComboBox(self)
		self.protocolCb = QComboBox(self)
		self.stimCbb = QComboBox(self)
		displayBtn = QPushButton("Display")
		appendBtn = QPushButton("Append")
		plotCtlGrid = QGridLayout()
		eles = (QLabel("Cell"), self.cellCb, QLabel("Trial"), self.trialCbb,
				self.trialCb, None, QLabel("Protocol"), self.protocolCb,
				self.stimCb, None, QLabel("Stim"), self.stimCbb,
				displayBtn, None, appendBtn, None)
		positions = [(i, j) for i in range(4) for j in range(4)]
		for ele, position in zip(eles, positions):
			if ele == None:
				continue
			else:
				plotCtlGrid.addWidget(ele, *position)
		ctlVB = QVBoxLayout()
		ctlVB.addLayout(projDispGrid)
		ctlVB.addLayout(plotCtlGrid)
		self.outText = QTextEdit(self)
		self.outText.setReadOnly(True)
		self.inText = QLineEdit(self)
		ioVB = QVBoxLayout()
		ioVB.addWidget(self.outText)
		ioVB.addWidget(self.inText)
		topHB = QHBoxLayout()
		topHB.addLayout(ctlVB)
		topHB.addLayout(ioVB)
		placeHolderWidget = QWidget()
		placeHolderWidget.setLayout(topHB)
		self.setCentralWidget(placeHolderWidget)

		# connections
		editProjBtn.clicked.connect(
				lambda: self.projDg.open(self.proj))
		self.projDg.edited.connect(self.updateProj)
		projNewAct.triggered.connect(lambda: self.saveProj("new"))
		projLoadAct.triggered.connect(self.loadProj)
		projSaveAct.triggered.connect(self.saveProj)
		projSaveAsAct.triggered.connect(lambda: self.saveProj("as"))
		exitAct.triggered.connect(self.close)
		selectCellBtn.clicked.connect(self.selectCells)
		assignTypBtn.clicked.connect(self.assignTyp)
		assignProtBtn.clicked.connect(self.assignProtSelect)
		self.cellCb.currentTextChanged.connect(self.updateTrials)
		displayBtn.clicked.connect(self.disp)
		appendBtn.clicked.connect(self.appDisp)
		self.stimCb.stateChanged.connect(self.updateProt)
		paramImportAct.triggered.connect(self.importParams)
		paramExportAct.triggered.connect(self.exportParams)
	
	def saveProj(self, mode = "save"):
		'''
		Manage saving project process.

		Parameters
		----------
		mode: string, optional
			Saving mode.
			"save" - Save to known project file, if not specified yet, 
				open a dialog to ask for a new one. Default.
			"new" - Create a new project, open a dialog to ask for a 
				new project file and clear current parameters.
			"as" - Save to a new project file, specified through dialogs.
		'''
		if mode == "new" and self.changeable():
			target = QFileDialog.getSaveFileName(self, "New project",
					self.proj.workDir + "/untitled.p")
			target = target[0]
			if len(target):
				self.proj = Project()
				self.proj.projFile = target
				self.proj.save(target)
				self.updateDisp()
		elif mode == "as" or len(self.proj.projFile) == 0:
			target = QFileDialog.getSaveFileName(self, "Save project as",
					self.proj.workDir + "/untitled.p")
			target = target[0]
			if len(target):
				self.proj.save(target)
		else:
			self.proj.save()
	
	def loadProj(self):
		'''
		Load project from a file specified using a dialog.
		'''
		if self.changeable():
			try:
				target = QFileDialog.getOpenFileName(self, "Load project")[0]
				if len(target):
					self.proj.load(target)
					self.updateDisp()
			except pickle.UnpicklingError:
				QMessageBox.warning(self, "Warning", "Wrong file format.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)

	@pyqtSlot(Project)
	def updateProj(self, prj):
		self.proj.edit(prj)
		self.updateDisp()
	
	def updateDisp(self):
		'''
		Update basic project parameters display. Also update display in modules.
		Also update cell and trial list comboboxes in the diplay region.
		'''
		self.projNameLb.setText("Name:" + self.proj.name)
		self.workDirLb.setText("Working Directory:" + self.proj.workDir)
		self.baseFldLb.setText("Raw Data Folder:" + self.proj.baseFolder)
		self.formatLb.setText("Data file name format:" + \
				self.proj.genName(1, 1))
		self.trialCb.setCheckState(Qt.Checked)
		# Also update module.
		self.updateModule()
		# Also update cell list.
		self.cellCb.clear()
		if len(self.proj.baseFolder):
			cl = self.proj.getCells()
			for c in cl:
				self.cellCb.addItem(str(c))
			self.cellCb.setCurrentIndex(0)
	
	@pyqtSlot(str)
	def updateTrials(self, cell):
		'''
		Update trial list in the display region when a cell is selected.

		Parameters
		----------
		cell: string
			Id of selected cell in the cell list.
		'''
		tl = self.proj.getTrials([int(cell)])
		self.trialCbb.clear()
		for t in tl:
			self.trialCbb.addItem(str(t))
	
	def updateModule(self):
		'''
		Update display of protocols in modules after changes.
		'''
		for _, m in self.analyzeWindows.items():
			m.updateDisp(False)

	def selectCells(self):
		'''
		Select cells that will be analyzed in this project.
		'''
		if self.changeable():
			try:
				inc = self.proj.getSelectedCells()
				exc = list(set(self.proj.getCells()) - set(inc))
				self.selectDg.selected.connect(self.proj.selectCells)
				self.selectDg.start(inc, exc)
			except FileNotFoundError:
				QMessageBox.warning(self, "Warning", "Base Folder not specified.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)
	
	def assignTyp(self):
		'''
		Dialogue window for assigned types to selected cells.
		'''
		if self.changeable():
			try:
				df = self.proj.getAssignedType()
				print(df["type"])
				assignDg = AssignDialog(df, self)
				assignDg.start()
				assignDg.assigned.connect(self.proj.assignType)
			except FileNotFoundError:
				QMessageBox.warning(self, "Warning", "Base Folder not specified.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)
	
	def assignProtSelect(self):
		'''
		Select cells for assigning protocols.
		'''
		if self.changeable():
			try:
				inc = self.proj.getSelectedCells()
				exc = list(set(self.proj.getCells()) - set(inc))
				self.selectDg.selected.connect(self.assignProt)
				self.selectDg.start(inc, exc)
			except FileNotFoundError:
				QMessageBox.warning(self, "Warning", "Base Folder not specified.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)
		
	@pyqtSlot(tuple)
	def assignProt(self, cells):
		'''
		Using assigning dialogue to assign protocols for trials in selected
		cells
		'''
		self.trialCb.setCheckState(Qt.Checked)
		trials = self.proj.getTrials(cells[0])
		df = pd.DataFrame([], index = pd.Index(trials, name = "trial"),
				columns = ["protocol"])
		df["protocol"] = ''
		print(df["protocol"])
		assignDg = AssignDialog(df, self)
		assignDg.start()
		assignDg.assigned.connect(lambda labels: 
				self.proj.assignProtocol(cells[0], labels))
		assignDg.assigned.connect(self.updateModule)
		self.selectDg.selected.connect(self.proj.selectCells)
	
	def disconnectSelectDg(self):
		'''
		Disconnect slots to selected signals when exiting cell selection 
		Dialog.
		'''
		self.selectDg.selected.disconnect()
	
	def display(self, win):
		'''
		Display the selected traces in a plotting window.

		Parameters
		----------
		win: PlotWindow
			Window in which the trace will be plotted.
		'''
		cid = int(self.cellCb.currentText())
		tid = int(self.trialCbb.currentText())
		trace, sr, _ = self.proj.loadWave(cid, tid)
		xt = np.arange(len(trace)) / sr
		win.plot(xt, trace, name = "cell{}_trial{}".format(cid, tid))
	
	def disp(self):
		'''
		Create a new plotting window and display traces.
		'''
		try:
			w = PlotWindow(self)
			self.plotWindows.append(w)
			w.focusInSig.connect(lambda: self.promotePlot(w))
			w.closeSig.connect(lambda: self.removePlotWin(w))
			self.display(w)
		except ValueError:
			w = self.plotWindows[-1]
			w.close()
			QMessageBox.warning(self, "Warning", "Wrong number.",
					QMessageBox.Ok)
		except FileNotFoundError as e:
			w = self.plotWindows[-1]
			w.close()
			QMessageBox.warning(self, "Warning", e.strerror, QMessageBox.Ok)

	def appDisp(self):
		'''
		Display trace by appending to active plot window.
		'''
		try:
			self.display(self.plotWindows[-1])
		except IndexError:
			QMessageBox.warning(self, "Warning", "Plot window doesn't exist.",
					QMessageBox.Ok)
		except ValueError:
			QMessageBox.warning(self, "Warning", "Wrong number.",
					QMessageBox.Ok)
		except FileNotFoundError as e:
			QMessageBox.warning(self, "Warning", e, QMessageBox.Ok)

	def promotePlot(self, pw):
		'''
		Promote a window as active window.
		'''
		print("Select plot window")
		i = self.plotWindows.index(pw)
		self.plotWindows.append(self.plotWindows.pop(i))

	def removePlotWin(self, pw):
		'''
		Promote a window as active window.
		'''
		print("Closed plot window")
		i = self.plotWindows.index(pw)
		self.plotWindows.pop(i)
		del(pw)
	
	def exportParams(self):
		'''
		Pop up a dialog to get a file directory and save current parameters
		to it.
		'''
		changed = 1
		for _, m in self.analyzeWindows.items():
			changed *= m.changeParams()
		if changed:
			target = QFileDialog.getSaveFileName(self, "Export parameters",
					self.proj.workDir + "/params.yml")[0]
			try:
				if len(target):
					self.param.save(target)
			except FileNotFoundError as e:
				QMessageBox.warning(self, "Warning", e.strerror, QMessageBox.Ok)
	
	def importParams(self):
		'''
		Pop up a dialog to get a file directory and read parameters from it.
		'''
		target = QFileDialog.getOpenFileName(self, "Import parameters",
				self.proj.workDir)[0]
		try:
			if len(target):
				self.param.load(target)
			for _, m in self.analyzeWindows.items():
				m.updateDisp()
		except FileNotFoundError as e:
			QMessageBox.warning(self, "Warning", e.strerror, QMessageBox.Ok)
		except UnicodeDecodeError:
			QMessageBox.warning(self, "Warninig", "Wrong format.")

	def addModule(self, name, module):
		'''
		Add analysis module to the program, making dialogue for controlling
		and parameter setting, making signal slot connections.

		Parameters
		----------
		name: string
			Name of this module, will be shown in the menu.
		module: class
			Module class use to define the instances to do the analysis.
		*args:
			Triplets of functionality names, the actual function in the 
			module to do the job and parameter key.
		'''
		m = module(self.inText, self.proj)
		m.textOut.connect(self.printTxt)
		m.plotOut.connect(self.plotTrace)
		m.plotLink.connect(self.linkTrace)
		m.plotClear.connect(self.clearTrace)
		self.modules.append(m)
		analyzeModAct = QAction(name, self)
		self.analysisMenu.addAction(analyzeModAct)
		analyzeModAct.triggered.connect(
				lambda: self.runModule(name, m))
	
	def runModule(self, name, module):
		'''
		Build the window to run the module if not built yet, otherwise
		set focus to that window.

		Parameters
		----------
		name: string
			Name of this module, will be shown in the menu.
		module: object
			Module class instance use to do the analysis.
		*args:
			Triplets of functionality names, the actual function in the 
			module to do the job and parameter key.
		'''
		if name in self.analyzeWindows:
			modWindow = self.analyzeWindows[name]
			modWindow.show()
		else:
			modWindow = AnalyzeModuleWindow(name, 
					module, self.param, self.proj, self)
			self.analyzeWindows[name] = modWindow
	
	def printTxt(self, text):
		'''
		Print text string in to output widget and update display.

		Parameters
		----------
		text: string
			To be printed.
		'''
		self.outText.append(text)
		self.outText.update()
	
	def plotTrace(self, plotDict):
		'''
		Make a new pyqtgraph window and plot intermediate results from
		analysis in it. If a window exists, plot in it.

		Parameters
		----------
		plotDict: dict
			Dictionary with plot and position data.
		'''
		if not hasattr(self, "traceWin") or self.traceWin == None:
			self.traceWin = SimplePlotWindow(self)
			self.traceWin.destroyed.connect(self.resetPlotWin)
		self.traceWin.showPlot(plotDict["item"], plotDict["pos"])
	
	def linkTrace(self, pos):
		'''
		Link trace axes in the traceWin.

		Parameters
		----------
		pos:
			Tuple of positions of axes.
		'''
		if hasattr(self, "traceWin") and self.traceWin != None:
			self.traceWin.linkPlot(pos[0], pos[1])
	
	def clearTrace(self):
		'''
		Remove everything in the plot window.
		'''
		if hasattr(self, "traceWin") and self.traceWin != None:
			self.traceWin.clear()
	
	def resetPlotWin(self):
		'''
		Reset attribute traceWin to None when the window is closed.
		'''
		self.traceWin = None
	
	@pyqtSlot(int)
	def updateProt(self, state):
		'''
		Update display of protocols in the ComboBox when the stimCb is 
		checked.
		'''
		if state == Qt.Checked:
			self.protocolCb.clear()
			pt = self.proj.getProtocols()
			for i in pt:
				self.protocolCb.addItem(i)
			self.protocolCb.update()
	
	def changeable(self):
		'''
		Check if analysis is running to determine if project properties
		and parameters are changeable.
		'''
		for _, m in self.analyzeWindows.items():
			if m.busy:
				return False
		return True
