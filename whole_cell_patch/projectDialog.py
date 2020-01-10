# Dialogue window for edit project parameters or create new project.

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, \
		QLineEdit, QDialog, QFileDialog
from .project import Project

class ProjectDialog(QDialog):
	'''
	Dialogue window for edit project parameters or create new project.
	'''
	edited = pyqtSignal(Project)

	def __init__(self, parent = None):
		'''
		Build window and show current project parameters if they exist.

		Parameters
		----------
		parent: QWidget, optional
			Parent object, default is None.
		'''
		super().__init__(parent)
		self.projNameTe = QLineEdit('')
		self.workDirTe = QLineEdit('')
		self.baseFolderTe = QLineEdit('')
		self.prefixTe = QLineEdit('')
		self.padTe = QLineEdit('')
		self.linkTe = QLineEdit('')
		self.suffixTe = QLineEdit('')
		workDirBtn = QPushButton("...")
		baseFolderBtn = QPushButton("...")
		saveBtn = QPushButton("OK")
		cancelBtn = QPushButton("Cancel")
		grids = (QLabel("Name:"), self.projNameTe, None, None,
				QLabel("Working Directory:"), self.workDirTe, workDirBtn, None,
				QLabel("Raw Data Folder:"), self.baseFolderTe, baseFolderBtn, None,
				QLabel("Prefix:"), self.prefixTe, QLabel("Pad:"), self.padTe,
				QLabel("Link:"), self.linkTe, QLabel("Suffix:"), self.suffixTe,
				None, saveBtn, cancelBtn, None)
		positions = [(i, j) for i in range(6) for j in range(4)]
		gridL = QGridLayout(self)
		for ele, pos in zip(grids, positions):
			if ele is not None:
				gridL.addWidget(ele, *pos)
		workDirBtn.clicked.connect(
				lambda: self.workDirTe.setText(
					QFileDialog.getExistingDirectory(self)))
		baseFolderBtn.clicked.connect(
				lambda: self.baseFolderTe.setText(
					QFileDialog.getExistingDirectory(self)))
		saveBtn.clicked.connect(self.save)
		cancelBtn.clicked.connect(self.reject)
	
	def open(self, prj):
		'''
		Update the contents in the blank spaces.

		Parameters
		----------
		prj: Project, optional
			Project object with project-wise parameters. Default is None,
			a new project will be created.
		'''
		self.projNameTe.setText(prj.name)
		self.workDirTe.setText(prj.workDir)
		self.baseFolderTe.setText(prj.baseFolder)
		self.prefixTe.setText(prj.formatParam["prefix"])
		self.padTe.setText(prj.formatParam["pad"])
		self.linkTe.setText(prj.formatParam["link"])
		self.suffixTe.setText(prj.formatParam["suffix"])
		self.update()
		super().open()

	def save(self):
		'''
		Excecute the functions and respond to button clicks.

		Signals
		-------
		edited:
			Signalling edit is confirmed with project object parameters.
		'''
		prj = Project('', self.projNameTe.text(), 
				self.baseFolderTe.text(), 
				self.workDirTe.text(),
				{"prefix": self.prefixTe.text(), 
					"pad": self.padTe.text(),
					"link": self.linkTe.text(),
					"suffix": self.suffixTe.text()})
		self.edited.emit(prj)
		self.accept()
