# Manage parameters in a grand parameter file for different types
# of analysis, including loading, setting and exporting.

import yaml

class ParamMan(object):
	'''
	Manage parameters used in the analysis modules, including 
	loading, setting and exporting.
	'''

	def __init__(self):
		'''
		Initializing by setting the parameters.

		Attributes
		----------
		params: dictionary
			Parameters in a dictionary. 
		'''
		self.params = {}
	
	def load(self, paramFile):
		'''
		Load parameters from yaml file.

		Parameters
		----------
		paramFile: string
			Parameter file directory.
		'''
		try:
			with open(paramFile, 'r') as f:
				tmp = yaml.load(f, Loader = yaml.FullLoader)
				for k in tmp:
					if k in self.params:
						self.params[k] = tmp[k]
		except IOError:
			print("File", paramFile, "not found.")
			raise
	
	def save(self, paramFile):
		'''
		Save parameters to a yaml file.

		Parameters
		----------
		paramFile: string
		'''
		try:
			with open(paramFile, 'r') as f:
				tmp = yaml.load(f, Loader = yaml.FullLoader)
				for k in self.params:
					# if k in tmp:
					tmp[k] = self.params[k]
		except IOError:
			tmp = self.params
		try:
			with open(paramFile, 'w') as f:
				f.write(yaml.dump(tmp))
		except IOError:
			print("Unable to open parameter file", paramFile,
					". Parameters not saved.")
			raise
	
	def get(self, target, default = {}):
		'''
		Get target parameter dictionary, after checking it has the 
		same keys as in the default. If any problem happened, default 
		will be returned.

		Parameters
		----------
		target: string
			Name of the target parameter dictionary.
		default: dictionary, optional
			Default parameters. Default is empty, no need when it's known
			for sure that the params has been set.

		Returns
		-------
		param: dictionary
			Target parameters.
		'''
		if self.params != None and target in self.params:
			param = self.params[target]
			return param
		elif self.params == None:
			self.params = {}
		self.params[target] = default
		return default
	
	def geti(self, default, target, key):
		'''
		Get specific parameter in target parameter dictionary.

		Parameters
		----------
		default: dictionary
			Default parameters.
		target: string
			Name of the target parameter dictionary.
		key: string
			Key of the specific parameter.

		Returns
		-------
		v: int, float or list
			Target parameter.
		'''
		params = self.get(default, target)
		v = params[key]
		return v

	def set(self, name, target):
		'''
		Set target parameter dictionary , using name as key.

		Parameters
		----------
		name: string
			Name key for the parameter dictionary to be saved.
		target: dictionary
			Target dictionary.
		'''
		if self.params == None:
			self.params = {}
		self.params[name] = target
	
	def seti(self, name, key, v):
		'''
		Set a specific parameter in a parameter dictionary for a function.
		Adjust to input values depending on the type of input.

		Parameters
		----------
		name: string
			Name key for the parameter dictionary.
		key: string
			Name key for the specific parameter to be set.
		v: int, float or list
			Parameter values.
		'''
		if type(v) == list and len(v) == 2 and \
				len(self.params[name][key]) == 2:
			if v[0] != None:
				self.params[name][key][0] = v[0]
			if v[1] != None:
				self.params[name][key][1] = v[1]
		else:
			self.params[name][key] = v
