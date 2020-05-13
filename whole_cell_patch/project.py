# Manage project raw data storage and project specific parameters.

import os
import re
import numpy as np
import pandas as pd
import pickle
from igor import binarywave
from PyQt5.QtCore import QObject, pyqtSlot
from .process import SignalProc


class Project(QObject, SignalProc):
	'''
	Contain functions used to manipulate raw data files.

	Attributes
	----------
	projFile: string
		Directory of the file saving the project information.
	name: string
		Name of the project, needs to be not empty in *create* mode.
	baseFolder: string
		Folder with the raw trace data, needs to be not empty in *create* 
		mode.
	workDir: string
		Working directory for saving the processing data and output results.
	formatParam: dictionary
		Raw trace file format parameters.
	assignedProt: dictionary, optional
		Trials and corresponding protocols used to record the trials.
	protocols: list
		Names of all protocols.
	assignedTyp: pandas.DataFrame, optional
		Cells and corresponding experimental types.
	types: list
		Names of all cell types.
	selectedCells: list
		Index of cells that are selected for analysis in this project
	'''
	def __init__(self, projFile = '', name = '', baseFolder = [],
			workDir = '', formatParam = {}):
		'''
		Create a new project with name, baseFolder and workDir or load a 
		project from saved file projFile.

		Parameters
		----------
		projFile: string, optional
			Directory of the file saving the project information. Default is empty,
			specified parameters will be used, otherwise, they'll be ignored.
		name: string, optional
			Name of the project, needs to be not empty in *create* mode. Default
			is empty.
		baseFolder: string, optional
			List of folders with the raw trace data, needs to be not empty in 
			*create* mode. Default is empty.
		workDir: string, optional
			Working directory for saving the processing data and output results.
			Default is empty.
		fileFormatDir: string, optional
			File with the raw trace file format parameters, default is empty.
		analysisParamFile: string, optional
			Directory to analysis parameter file, the parameters are managed by 
			another class.
		'''
		super().__init__()
		self.projFile = projFile
		if len(projFile) == 0:
			self.name = name
			self.workDir = workDir
			if len(workDir) and workDir[-1] != os.sep:
				self.workDir += os.sep
			self.baseFolder = baseFolder
			for i in range(len(self.baseFolder)):
				if self.baseFolder[i][-1] != os.sep:
					self.baseFolder[i] += os.sep
			if len(formatParam):
				self.formatParam = formatParam
			else:
				self.formatParam = {"prefix": "Cell",
					"pad": '4', 
					"link": '_', 
					"suffix": ".ibw"}
		else:
			self.load(projFile)
		self.filters = []

	def edit(self, dummy):
		'''
		Edit basic project information based the attributes in a dummy class.

		Parameters
		----------
		dummy: Project
			Dummy project with only basic project attributes specified.
		'''
		self.name = dummy.name
		self.baseFolder = dummy.baseFolder
		self.workDir = dummy.workDir
		self.formatParam = dummy.formatParam
			
	def load(self, projFile):
		'''
		Load project information from project file.

		Parameters
		----------
		projFile: string
			Directory of the file with the project information.
		'''
		with open(projFile, 'rb') as f:
			info = pickle.load(f)
		self.projFile = projFile
		self.name = info["name"]
		self.baseFolder = info["baseFolder"]
		self.workDir = info["workDir"]
		self.formatParam = info["formatParam"]
		if "assignedProt" in info:
			self.assignedProt = info["assignedProt"]
			self.protocols = info["protocols"]
		if "assignedTyp" in info:
			self.assignedTyp = info["assignedTyp"]
			self.types = info["types"]
		if "selectedCells" in info:
			self.selectedCells = info["selectedCells"]

	def save(self, target = ''):
		'''
		Save project information into a file.

		Parameters
		----------
		target: string, optional
			Direcoty of target file to save the information. Default is
			empty, in which case it will be saved in a current projFile.
			If projFile is empty, do nothing.
		'''
		info = {}
		info["name"] = self.name
		info["baseFolder"] = self.baseFolder
		info["workDir"] = self.workDir
		info["formatParam"] = self.formatParam
		if hasattr(self, "assignedProt") and len(self.assignedProt):
			info["protocols"] = self.protocols
			info["assignedProt"] = self.assignedProt
		if hasattr(self, "assignedTyp") and len(self.assignedTyp):
			info["types"] = self.types
			info["assignedTyp"] = self.assignedTyp
		if hasattr(self, "selectedCells") and len(self.selectedCells):
			info["selectedCells"] = self.selectedCells
		if len(target) == 0:
			target = self.projFile
		else:
			self.projFile = target
		if len(target):
			with open(target, 'wb') as f:
				pickle.dump(info, f)

	def genName(self, cell, trial):
		'''
		Generate raw data file name of certain trial of certain cell.

		Parameters
		----------
		cell: int
			Cell index.
		trial: int
			Trial index.

		Returns
		-------
		fileName: string
			Formated file name.
		'''
		cell = int(cell)
		trial = int(trial)
		p = self.formatParam
		fileName = (p['prefix'] + p['link'] + '{0:0' + p['pad'] + 'd}' + 
				p['link'] + '{1:0' + p['pad'] + 'd}' + 
				p['suffix']).format(cell, trial)
		return fileName

	@pyqtSlot(tuple)
	def selectCells(self, cells):
		'''
		Select cells that will be analyzed in this project.

		Parameters
		----------
		cells: tuple
			In the form of (inc, exc), in which inc is a list of included
			cells and exc is a list of excluded cells.
		'''
		self.selectedCells = sorted(cells[0])
		# If cell types have been assigned before, adjust it
		# by keeping only the newly selected cells and assign unknown
		# type to those that are not assigned before.
		if hasattr(self, "assignedTyp"):
			updated = pd.DataFrame([], 
					index = pd.Index(self.selectedCells, name = "cell"))
			self.assignedTyp = updated.merge(self.assignedTyp, how = "left", 
					on = "cell", sort = True).fillna("unknown")
			self.types = set(self.assignedTyp["type"])
	
	def getSelectedCells(self):
		'''
		Get cells selected for analysis in this project.

		Returns
		-------
		cells: list
			Sorted list of indices of selected cells. If none has been
			selected, use all the cells.
		'''
		if hasattr(self, "selectedCells"):
			return self.selectedCells
		else:
			return self.getCells()

	def assignProtocol(self, cells, labels):
		'''
		Assign trials to different protocols for different analysis.
		Take labeled trial data or labeled stimulation type name
		data.

		Parameters
		----------
		cells: array_like
			Id of cells to assign protocols. When it has length of 0,
			all the cells in the baseFolder will be considered.
		labels: pandas.DataFrame or dict
			pandas.DataFrame - 
				Trial and protocol pairs in a DataFrame with two columns,
				"trial" and "protocol", "trial" as index. The same
				trial-protocol association will be applied to all cells.
			dict - 
				Dictionary with cell ids as keys and trial-protocol pair
				data in a DataFrame as values. Specify protocols for
				cells separatedly.

		Attributes
		----------
		protocols: set
			Names of protocols.
		assignedProt: dictionary
			Dictionary with cells as keys and trial-protocol pairs
			DataFrame as values.
		'''
		# drop empty labels
		if type(labels) is not dict:
			labels.drop(labels.index[labels["protocol"] == ''], inplace = True)
		if len(cells) == 0:
			cells = self.getCells()
		if not hasattr(self, "assignedProt"):
			self.assignedProt = {}
		for c in cells:
			if type(labels) is dict:
				self.assignedProt[c] = labels[c]
			else:
				cTrials = self.getTrials([c])
				labeled = list(set(cTrials) & set(labels.index))
				prot = labels.loc[labeled, :]
				# record the simulation intensity of the trials as well.
				prot["stim"] = np.nan
				for t in labeled:
					_, _, stim = self.loadWave(c, t)
					prot.loc[t, "stim"] = stim[2]
				self.assignedProt[c] = prot
		# update protocols by checking again all protocl tables
		self.protocols = set()
		for c, df in self.assignedProt.items():
			self.protocols = self.protocols | set(df["protocol"])
	
	def getStimType(self, cells, trials):
		'''
		Returns stimulation type for trials for setting protocol based 
		on stimulation type.

		Parameters
		----------
		cells: array_like
			Cells of which the stimulation type will be returned.
		trials: array_like
			Trials of which the stimulation type will be returned.

		Returns
		-------
		stimTypes: pandas.DataFrame
			Cells and trials as index, one column with stimulation
			amplitude and one column with the stimulation type.
		'''
		stimTypes = []
		for c in cells:
			for t in trials:
				try:
					trace, sr, stim = self.loadWave(c, t)
					stimTypes.append([c, t, stim[2], stim[3]])
				except IOError:
					pass
		stimTypes = pd.DataFrame(stimTypes, 
				columns = ("cell", "trial", "stim", "type"))
		return stimTypes

	def getProtocols(self):
		'''
		Get all the protocols specified in this project. If not yet,
		return empty set.
		'''
		if hasattr(self, "protocols"):
			return self.protocols
		else:
			return set()
	
	@pyqtSlot(pd.DataFrame)
	def assignType(self, labels):
		'''
		Assign cells to different types for possible statistical tests.

		Parameters
		----------
		labels: pandas.DataFrame
			Cell and type pairs in a DataFrame with two columns,
			"cell" and "type", "cell" as index.

		Attributes
		----------
		types: set
			Names of protocols.
		assignedTyp: pandas.DataFrame
			Cell and type pairs in a DataFrame with two columns,
			"cell" and "type", "cell" as index.
		'''
		self.types = set(labels["type"])
		self.assignedTyp = labels
		print(self.assignedTyp)
	
	def getAssignedType(self):
		'''
		Get assigned types in the form of a pandas DataFrame, if not
		specified yet, return an empty one.

		Returns
		-------
		labels: pd.DataFrame
			Cell and type pairs in a DataFrame with two columns,
			"cell" and "type", "cell" as index.
		'''
		if hasattr(self, "assignedTyp"):
			return self.assignedTyp
		else:
			labels = pd.DataFrame([], 
					index = pd.Index(self.getSelectedCells(), name = "cell"),
					columns = ["type"])
			return labels

	def getCells(self):
		'''
		Get list of cell ids in the baseFolder.

		Returns
		-------
		cells: list
			Cell ids.
		'''
		for bf in self.baseFolder:
			dfs = os.listdir(bf)
			cells = set() 
			for df in dfs:
				matched = re.match(self.formatParam['prefix'] + \
						self.formatParam['link'] + \
						'0*([1-9][0-9]*)' + \
						self.formatParam['link'] + \
						'0*([1-9][0-9]*)' + \
						self.formatParam['suffix'] , df)
				if matched:
					cells.add(int(matched.group(1)))
			return list(cells)

	def getTrials(self, cells, protocol = None, stim = None):
		'''
		Get list of trial ids for cells in the baseFolder. If there is more
		than one cell, list the union of trials from each cell. If protocol
		and stim are provided, trials will be selected from saved protocol
		stim table.

		Parameters
		----------
		cells: array_like
			Cell ids. If length is 0, all cells in the baseFolder will be 
			considered.
		protocol: string, optional
			Protocol used to limit trials to get. Default not considered.
		stim: float, optional
			Stimulation amplitude used to limit trials to get. Default 
			not considered.

		Returns
		-------
		trials: list
			Trial ids.
		'''
		trials = set() 
		if protocol is None or stim is None:
			for bf in self.baseFolder:
				dfs = os.listdir(bf)
				for c in cells:
					for df in dfs:
						matched = re.match(self.formatParam['prefix'] + \
								self.formatParam['link'] + \
								'{:04d}'.format(c) + \
								self.formatParam['link'] + \
								'0*([1-9][0-9]*)' + \
								self.formatParam['suffix'] , df)
						if matched:
							trials.add(int(matched.group(1)))
		elif hasattr(self, "assignedProt"):
			for c in cells:
				prot = self.assignedProt[c]
				ts = set(prot.index[(prot["protocol"] == protocol) &
						(abs(prot["stim"] - stim) < 1e-12)])
				trials = trials | ts
		return list(trials)

	def getStims(self, cell, protocol):
		'''
		Get list of stimulation amplitude for cell in protocol.
		'''
		stims = []
		if hasattr(self, "assignedProt"):
			if cell in self.assignedProt:
				prot = self.assignedProt[cell]
				if "stim" in prot.columns:
					stims = set(prot.loc[prot["protocol"] == protocol, "stim"])
		return list(stims)

	def setFilters(self, filters = []):
		'''
		Set filters to be applied on the traces when loading them. The
		filter parameters need to be converted to numertic format. Also
		check the parameters, if not valid, default will be used and returns
		0. Otherwise returns 1.

		Parameters
		----------
		filters: list
			List of filters defined in dictionaries. Parameters are
			in string format.

		Returns
		-------
		ret: int
			0 when invalid paramter detected, 1 normally.
		'''
		ret = 1
		self.filters = []
		default = self.getDefaultFilters()
		for f in filters:
			name = f["name"]
			fc = {}
			try:
				if name == "median":
					fc["name"] = name
					fc["winSize"] = int(f["winSize"])
					fc["threshold"] = float(f["threshold"])
				else:
					fc["name"] = name
					for k, v in f.items():
						if k != "name":
							fc[k] = float(v)
					if (name == "bessel,bandpass" or \
							name == "butter,bandpass") and \
							fc["freq_high"] <= fc["freq_low"]:
								ret = 0
								for d in default:
									if d["name"] == name:
										fc = d
			except ValueError as e:
				ret = 0
				for d in default:
					if d["name"] == name:
						fc = d
			self.filters.append(fc)
		return ret

	def getDefaultFilters(self, form = "num"):
		'''
		Define available filter types and default parameters.

		Paramters
		---------
		form: str
			Format of the filter parameters.
			"num" - numeric, for setting.
			"str" - string, for displaying.
		'''
		if form == "num":
			filters = [{"name": "median", 
				"winSize": 5, 
				"threshold": 30e-12}, 
				{"name": "butter,lowpass",
					"freq": 500},
				{"name": "butter,highpass",
					"freq": 2000},
				{"name": "butter,bandpass",
					"freq_low": 500,
					"freq_high": 2000},
				{"name": "bessel,lowpass",
					"freq": 500},
				{"name": "bessel,highpass",
					"freq": 2000},
				{"name": "bessel,bandpass",
					"freq_low": 500,
					"freq_high": 2000}]
		else:
			filters = [{"name": "median", 
				"winSize": '5', 
				"threshold": "30e-12"}, 
				{"name": "butter,lowpass",
					"freq": "500"},
				{"name": "butter,highpass",
					"freq": "2000"},
				{"name": "butter,bandpass",
					"freq_low": "500",
					"freq_high": "2000"},
				{"name": "bessel,lowpass",
					"freq": "500"},
				{"name": "bessel,highpass",
					"freq": "2000"},
				{"name": "bessel,bandpass",
					"freq_low": "500",
					"freq_high": "2000"}]
		return filters
		
	def loadWave(self, cell, trial):
		'''
		Load trace from an igor data file, as well as sampleing rate 
		and stimulation amplitude.

		Parameters
		----------
			cell: int
				Cell index.
			trial: int
				Trial index.

		Returns
		-------
			trace: numpy.array
				Data trace in the file.
			sr: float
				Sampling rate.
			stim: list
				Stimulation step properties, including start time,
				duration and amplitude
		'''
			
		try:
			sr, stim_amp, stim_dur, stim_start = 10000, 0, 0, 0
			stim_type = ''
			for bf in self.baseFolder:
				dfs = os.listdir(bf)
				if self.genName(cell, trial) in dfs:
					break
			data = binarywave.load(bf + self.genName(cell, trial))
			trace = data['wave']['wData']
			# Search for sampling rate
			searched = re.search(r'XDelta\(s\):(.*?);', 
					data['wave']['note'].decode())
			if(searched != None):
				sr = 1 / float(searched.group(1))
			# Search for stimulation amplitude
			searched = re.search(r';Stim Amp.:(.+?);', 
					data['wave']['note'].decode())
			if(searched != None):
				stim_amp = float(searched.group(1))
			# Search for stimulation duration
			searched = re.search(r';Width:(.+?);', 
					data['wave']['note'].decode())
			if(searched != None):
				stim_dur = float(searched.group(1))
			# Search for stimulation start
			searched = re.search(r';StepStart\(s\):(.+?);', 
					data['wave']['note'].decode())
			if(searched != None):
				stim_start = float(searched.group(1))
			# Search for stimulation type
			searched = re.search(r';StimProtocol:(.+?);', 
					data['wave']['note'].decode())
			if(searched != None):
				stim_type = searched.group(1)
			if len(self.filters):
				for f in self.filters:
					names = f["name"].split(',')
					if len(names) == 1:
						trace = self.thmedfilt(trace, f["winSize"], 
								f["threshold"])
					elif names[1] == "bandpass":
						trace = self.smooth(trace, sr, 
								[f["freq_low"], f["freq_high"]], names[0], names[1])
					else:
						trace = self.smooth(trace, sr, 
								f["freq"], names[0], names[1])
			return (trace, sr, [stim_start, stim_dur, stim_amp, stim_type])
		except IOError:
			print('Igor wave file (' + bf + self.genName(cell, trial)
					+ ') reading error')
			raise
	
	def iterate(self, protocol = None):
		'''
		Iterate all trace files in a protocol, yield cell 
		and trial numbers.

		Parameters
		----------
		protocol: string, optional
			Name of protocol used on a specific set of trials in each cell.
			Default is empty, in which case all trials will be tranversed.

		Yields
		------
		c: int
			Cell number.
		t: int
			Trial number.
		'''
		if protocol is not None and len(protocol) and \
				hasattr(self, "assignedProt"):
			for c in self.getSelectedCells():
				if c in self.assignedProt:
					lb = self.assignedProt[c]
					for t in lb.index:
						if lb.loc[t, "protocol"] == protocol:
							yield (c, t)
		elif protocol is None:
			cells = self.getCells()
			for c in cells:
				for t in self.getTrials([c]):
					yield (c, t)
	
	def getTrialTable(self, protocol, cells = [], trials = [],
			types = [], stims = []):
		'''
		Return a table with type, stimulation amplitude, cell id and
		trial id as columns. Each row is a trial.

		Parameters
		----------
		protocol: string
			Protocol where the subthreshold recording is done.
		cells: array_like, optional
			Ids of cells to include. By default include all the cells.
		trials: array_like, optional
			Ids of trials to include. By default include all trials.
		types: array_like, optional
			Types of cells to include. By default include all the cells.
		stims: array_like, optional
			Stimulation amplitudes with which trials will be included.
			By default include all trials.

		Returns
		-------
		df: pandas.DataFrame
			Table with trial labels, "type", "stim", "cell" and "trial".
		'''
		df = []
		if len(protocol) and hasattr(self, "assignedProt"):
			if len(cells):
				cells = list(set(cells) & set(self.getSelectedCells()))
			else:
				cells = self.getSelectedCells()
			for c in cells:
				if c in self.assignedProt and ((not len(types)) or \
						self.assignedTyp.loc[c, "type"] in types):
					lb = self.assignedProt[c]
					if len(trials):
						ctrials = np.unique(trials + list(lb.index))
					else:
						ctrials = lb.index
					for t in ctrials:
						if lb.loc[t, "protocol"] == protocol and \
								((not len(stims)) or lb.loc[t, "stim"] in stims):
							df.append([self.assignedTyp.loc[c, "type"], 
								lb.loc[t, "stim"], c, t])
		df = pd.DataFrame(df, columns = ["type", "stim", "cell", "trial"])
		return df

	def clear(self):
		'''
		Clear current content to make a new project object.
		'''
		self.projFile = ''
		self.name = ''
		self.baseFolder = ''
		self.workDir = ''
		self.formatParam = {"prefix": "Cell",
			"pad": '4', 
			"link": '_', 
			"suffix": ".ibw"}
		if hasattr(self, "assignedProt"):
			del self.protocols
			del self.assignedProt
		if hasattr(self, "assignedTyp"):
			del self.types
			del self.assignedTyp
		if hasattr(self, "selectedCells"):
			del self.selectedCells
