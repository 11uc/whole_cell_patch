# Main window and functions of the ephys analysis program

import sys
from PyQt5.QtCore import Qt, pyqtSlot, QEvent
from PyQt5.QtWidgets import QMainWindow, QAction, QLabel, QGridLayout, \
		QPushButton, QButtonGroup, QRadioButton, QVBoxLayout, QHBoxLayout, \
		QTextEdit, QWidget, QFileDialog, QApplication, QCheckBox,\
		QMessageBox, QLineEdit, QComboBox
import pickle
import numpy as np
import pandas as pd
from .ap import AP
from .sealTest import SealTest
from .mini import Mini
from .sub import Sub
from .multiPlot import MultiPlot
from .analyzeModule import AnalyzeModuleWindow
from .project import Project
from .param import ParamMan
from .projectDialog import ProjectDialog
from .selectCellDialog import SelectCellDialog
from .assignDialog import AssignDialog
from .plotWindow import PlotWindow, SimplePlotWindow
from .filterWin import FilterWin

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
		self.selectDg.rejected.connect(self.disconnectSelectDg)
		self.filterDg = FilterWin(self.proj.getDefaultFilters("str"), 
				parent = self)
		self.plotWindows = []
		self.analyzeWindows = {}
		self.initUI()
		self.modules = []  # list with all the modules
		self.addModule("Action potential", AP)
		self.addModule("Seal test", SealTest)
		self.addModule("Mini analysis", Mini)
		self.addModule("Subthreshold response analysis", Sub)
		self.addModule("Multiple trace plot", MultiPlot)
		self.show()
	
	def initUI(self):
		'''
		Build the UI, all analysis functions are in the menu and the
		main window has controls for browsing the traces.
		'''
		menubar = self.menuBar()
		menubar.setNativeMenuBar(False)
		fileMenu = menubar.addMenu("&File")
		projectMenu = menubar.addMenu("Project")
		self.analysisMenu = menubar.addMenu("&Analysis")
		processMenu = menubar.addMenu("Process")

		projNewAct = QAction("New project", self)
		projLoadAct = QAction("Load project", self)
		projSaveAct = QAction("Save project", self)
		projSaveAsAct = QAction("Save project as", self)
		exitAct = QAction("Exit", self)
		exitAct.setShortcut("Ctrl + Q")
		paramImportAct = QAction("Import parameters", self)
		paramExportAct = QAction("Export parameters", self)
		filterAct = QAction("Filtering", self)
		
		fileMenu.addAction(projNewAct)
		fileMenu.addAction(projLoadAct)
		fileMenu.addAction(projSaveAct)
		fileMenu.addAction(projSaveAsAct)
		fileMenu.addAction(exitAct)
		self.analysisMenu.addAction(paramImportAct)
		self.analysisMenu.addAction(paramExportAct)
		self.analysisMenu.addSeparator()
		processMenu.addAction(filterAct)

		self.projNameLb = QLabel("Name:")
		self.workDirLb = QLabel("Working Directory:")
		self.baseFldLb = QLabel("Raw Data Folder:")
		self.formatLb = QLabel("Data file name format:")
		eles = (self.projNameLb, self.workDirLb, self.baseFldLb,
				self.formatLb)
		projDispGrid = QGridLayout()
		for i, ele in enumerate(eles):
			projDispGrid.addWidget(ele, i, 0)
		editProjAct = QAction("Edit project", self)
		selectCellAct = QAction("Select cells", self)
		assignProtTAct = QAction("Assign by trials", self)
		assignProtSAct = QAction("Assign by stimulus type", self)
		assignTypAct = QAction("Assign cell types", self)
		projectMenu.addAction(editProjAct)
		projectMenu.addAction(selectCellAct)
		assignProtMenu = projectMenu.addMenu("Assign protocol")
		assignProtMenu.addAction(assignProtTAct)
		assignProtMenu.addAction(assignProtSAct)
		projectMenu.addAction(assignTypAct)

		self.cellCb = QComboBox(self)
		optionBg = QButtonGroup(self)
		optionBg.setExclusive(True)
		self.trialRb = QRadioButton("Trial")
		self.stimRb = QRadioButton("Stim")
		optionBg.addButton(self.trialRb)
		optionBg.addButton(self.stimRb)
		self.trialRb.setChecked(True)
		self.trialCbb = QComboBox(self)
		self.protocolCb = QComboBox(self)
		self.stimCbb = QComboBox(self)
		self.normCb = QCheckBox("Normalize")
		self.normWin1Le = QLineEdit(self)
		self.normWin2Le = QLineEdit(self)
		displayBtn = QPushButton("Display")
		appendBtn = QPushButton("Append")
		plotCtlGrid = QGridLayout()
		eles = (QLabel("Cell"), self.cellCb, QLabel("Trial"), self.trialCbb,
				self.trialRb, None, QLabel("Protocol"), self.protocolCb,
				self.stimRb, None, QLabel("Stim"), self.stimCbb,
				self.normCb, QLabel("Window"), self.normWin1Le, self.normWin2Le,
				displayBtn, None, appendBtn, None)
		positions = [(i, j) for i in range(5) for j in range(4)]
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

		self.projDg.edited.connect(self.updateProj)
		projNewAct.triggered.connect(lambda: self.saveProj("new"))
		projLoadAct.triggered.connect(self.loadProj)
		projSaveAct.triggered.connect(self.saveProj)
		projSaveAsAct.triggered.connect(lambda: self.saveProj("as"))
		exitAct.triggered.connect(self.close)
		editProjAct.triggered.connect(lambda: self.projDg.open(self.proj))
		selectCellAct.triggered.connect(self.selectCells)
		assignTypAct.triggered.connect(self.assignTyp)
		assignProtTAct.triggered.connect(self.assignProtByTrialSelect)
		assignProtSAct.triggered.connect(self.assignProtByTypeSelectCell)
		self.trialRb.clicked.connect(self.updateTrialsBySelection)
		self.stimRb.clicked.connect(self.updateProtocols)
		self.cellCb.currentTextChanged.connect(self.updateTrialsByCell)
		self.cellCb.currentTextChanged.connect(self.updateStimsByCellOrProtocol)
		self.protocolCb.currentTextChanged.connect(self.updateStimsByCellOrProtocol)
		self.stimCbb.currentTextChanged.connect(self.updateTrialsByStim)
		displayBtn.clicked.connect(self.disp)
		appendBtn.clicked.connect(self.appDisp)
		paramImportAct.triggered.connect(self.importParams)
		paramExportAct.triggered.connect(self.exportParams)
		filterAct.triggered.connect(self.filterDg.show)
		self.filterDg.filterApplied.connect(self.setFilters)
	
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
				self.proj.clear()
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
					self.filterDg.applyFilters(0)  # apply filters to this project
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
		self.baseFldLb.setText("Raw Data Folder:" + 
				'\n'.join(self.proj.baseFolder))
		self.formatLb.setText("Data file name format:" + \
				self.proj.genName(1, 1))
		self.trialRb.setChecked(True)
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
	def updateTrialsByCell(self, cell):
		'''
		Update trial list in the display region when a cell is selected.

		Parameters
		----------
		cell: string
			Id of selected cell in the cell list.
		'''
		if len(cell) and self.trialRb.isChecked():
			tl = self.proj.getTrials([int(cell)])
			self.trialCbb.clear()
			for t in tl:
				self.trialCbb.addItem(str(t))
	
	@pyqtSlot(str)
	def updateTrialsByStim(self, stim):
		'''
		Update trial list when a stimuation is selected.

		Parameters
		----------
		stim: string
			Stimualtion from the stimulation list.
		'''
		if len(stim):
			c = int(self.cellCb.currentText())
			p = self.protocolCb.currentText()
			s = float(self.stimCbb.currentText())
			tl = self.proj.getTrials([c], p, s)
			self.trialCbb.clear()
			for t in tl:
				self.trialCbb.addItem(str(t))

	def updateTrialsBySelection(self, _):
		'''
		Update the trial list when display by trial mode is selected.
		'''
		c = self.cellCb.currentText()
		if len(c):
			tl = self.proj.getTrials([int(c)])
			self.trialCbb.clear()
			for t in tl:
				self.trialCbb.addItem(str(t))

	def updateProtocols(self, _):
		'''
		Update protocol list in the display region when display by stimulation
		mode is selected.
		'''
		pl = self.proj.getProtocols()
		self.protocolCb.clear()
		if len(pl):
			for p in pl:
				self.protocolCb.addItem(p)
			self.protocolCb.setCurrentIndex(0)

	@pyqtSlot(str)
	def updateStimsByCellOrProtocol(self, arg):
		'''
		Update stimulation list in the display region when a new protocol
		is selected or a new cell is selected.
		'''
		# only update when display by stimulation mode is selected.
		if self.stimRb.isChecked():
			c = int(self.cellCb.currentText())
			p = self.protocolCb.currentText()
			sl = self.proj.getStims(c, p)
			self.stimCbb.clear()
			for s in sl:
				self.stimCbb.addItem(str(s))
			if len(sl):
				self.stimCbb.setCurrentIndex(0)
	
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
			except (FileNotFoundError, TypeError):
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
				assignDg = AssignDialog(df, self)
				assignDg.start()
				assignDg.assigned.connect(self.proj.assignType)
			except FileNotFoundError:
				QMessageBox.warning(self, "Warning", "Base Folder not specified.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)
	
	def assignProtByTrialSelect(self):
		'''
		Select cells for assigning protocols.
		'''
		if self.changeable():
			try:
				inc = self.proj.getSelectedCells()
				exc = list(set(self.proj.getCells()) - set(inc))
				self.selectDg.selected.connect(self.assignProtByTrial)
				self.selectDg.start(inc, exc)
			except FileNotFoundError:
				QMessageBox.warning(self, "Warning", "Base Folder not specified.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)
		
	@pyqtSlot(tuple)
	def assignProtByTrial(self, cells):
		'''
		Using assigning dialogue to assign protocols for trials in selected
		cells
		'''
		self.trialRb.setChecked(True)
		trials = self.proj.getTrials(cells[0])
		df = pd.DataFrame([], index = pd.Index(trials, name = "trial"),
				columns = ["protocol"])
		df["protocol"] = ''
		assignDg = AssignDialog(df, self)
		assignDg.start()
		assignDg.assigned.connect(lambda labels: 
				self.proj.assignProtocol(cells[0], labels))
		assignDg.assigned.connect(self.updateModule)
		self.disconnectSelectDg()
		self.selectDg.selected.connect(self.proj.selectCells)
	
	def assignProtByTypeSelectCell(self):
		'''
		Select cells for assigning protocols by stimulation type.
		'''
		if self.changeable():
			try:
				inc = self.proj.getSelectedCells()
				exc = list(set(self.proj.getCells()) - set(inc))
				self.selectDg.changeTarget("Cells")
				self.selectDg.selected.connect(self.assignProtByTypeSelectTrial)
				self.selectDg.start(inc, exc)
			except FileNotFoundError:
				QMessageBox.warning(self, "Warning", "Base Folder not specified.",
						QMessageBox.Ok)
		else:
			QMessageBox.warning(self, "Warning", "Analysis running.",
					QMessageBox.Ok)

	@pyqtSlot(tuple)
	def assignProtByTypeSelectTrial(self, cells):
		'''
		Select trials for assigning protocols by stimulation type.

		Parameters
		----------
		cells: tuple
			Selected cells.

		Attribute
		---------
		cellsForProtAssign: tuple
			Selected cells, temporary used for assigning protocol by types.
		'''
		self.cellsForProtAssign = cells[0]
		inc = self.proj.getTrials(cells[0])
		exc = []
		self.selectDg.changeTarget("Trials")
		self.selectDg.selected.disconnect()
		self.selectDg.selected.connect(self.assignProtByType)
		self.selectDg.start(inc, exc)

	@pyqtSlot(tuple)
	def assignProtByType(self, trials):
		'''
		Assign protocols based on stimulation types of trials from 
		self.cellsForProtAssign.
		'''
		self.disconnectSelectDg()
		self.trialRb.setChecked(True)
		stimTypes = self.proj.getStimType(self.cellsForProtAssign, trials[0])
		types = np.unique(stimTypes["type"])
		df = pd.DataFrame([], index = pd.Index(types, name = "stim"),
				columns = ["protocol"])
		df["protocol"] = ''
		assignDg = AssignDialog(df, self)
		ret = assignDg.exec_()
		if ret:
			df = assignDg.df
			stimTypes["protocol"] = ''
			for i in df.index:
				stimTypes.loc[stimTypes["type"] == i, "protocol"] = \
						df.loc[i, "protocol"]
			prot = {}
			cells = np.unique(stimTypes["cell"])
			for c in cells:
				prot[c] = stimTypes.loc[stimTypes["cell"] == c,
						["trial", "stim", "protocol"]].set_index("trial")
			self.proj.assignProtocol(cells, prot)
			self.updateModule()

	def disconnectSelectDg(self):
		'''
		Disconnect slots to selected signals when exiting cell selection 
		Dialog. Also reset the displayed target.
		'''
		self.selectDg.selected.disconnect()
		self.selectDg.changeTarget('')
	
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
		# normalize to baseline
		if self.normCb.isChecked():
			win1 = int(sr * float(self.normWin1Le.text()))
			win2 = int(sr * float(self.normWin2Le.text()))
			assert win2 > win1 and 0 <= win1 and win2 <= len(trace)
			trace_ = trace - np.mean(trace[win1:win2])
			win.plot(xt, trace_, name = "cell{}_trial{}_norm".format(cid, tid))
		else:
			trace_ = trace
			win.plot(xt, trace_, name = "cell{}_trial{}".format(cid, tid))
	
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
		except FileNotFoundError as e:
			w = self.plotWindows[-1]
			w.close()
			QMessageBox.warning(self, "Warning", e.strerror, QMessageBox.Ok)
		except (ValueError, AssertionError):
			w = self.plotWindows[-1]
			w.close()
			QMessageBox.warning(self, "Warning", "Wrong number.",
					QMessageBox.Ok)

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
		i = self.plotWindows.index(pw)
		self.plotWindows.append(self.plotWindows.pop(i))

	def removePlotWin(self, pw):
		'''
		Promote a window as active window.
		'''
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
		except (UnicodeDecodeError, KeyError):
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
		# update parameters with default parameters
		_, prof = m.profile()
		self.param.set("basic_" + name, m.loadDefault("basic"))  # basic
		for p in prof:
			self.param.set(p["pname"], m.loadDefault(p["pname"]))
	
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
			modWindow.updateDisp()
	
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
			Dictionary with plot paramters and position data.
		'''
		if not hasattr(self, "traceWin") or self.traceWin == None:
			self.traceWin = SimplePlotWindow(self)
			self.traceWin.destroyed.connect(self.resetPlotWin)
		self.traceWin.showPlot(plotDict["params"], plotDict["pos"])
	
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
	
	def changeable(self):
		'''
		Check if analysis is running to determine if project properties
		and parameters are changeable.
		'''
		for _, m in self.analyzeWindows.items():
			if m.busy:
				return False
		return True

	def setFilters(self, fs):
		'''
		Set filters to be applied when loading traces.

		Parameters
		----------
		fs: list
			List of dictionaries with user defined filter information.
		'''
		ret = self.proj.setFilters(fs)
		if not ret:
			QMessageBox.warning(self, "Warning", 
					"Wrong filter format, default used.", QMessageBox.Ok)
