# Add keyboard shorcut to make copy and paste in QTableWidget easier.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QTableWidget, QShortcut

class CpTableWidget(QTableWidget):
	'''
	With function and key press responses to enable copy/paste without
	entering edit mode and multiple cell paste. Also enable deletion
	in multiple cells.
	'''
	def __init__(self, *args):
		'''
		Initialize attributes, add shortcuts.

		Attributes
		----------
		copied: list
			List of string in cells that are copied.
		'''
		super().__init__(*args)
		self.copied = []
		s1 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_C), self)
		s1.activated.connect(self.copy)
		s2 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_V), self)
		s2.activated.connect(self.paste)

	def copy(self):
		'''
		Copy text from selected item(s).
		'''
		self.copied.clear()
		for it in self.selectedItems():
			if it == None:
				self.copied.append('')
			else:
				self.copied.append(it.text())

	def paste(self):
		'''
		Paste copeid texts. If more items are copied than cells to paste, 
		paste the first few cells until paste cells are filled. If less items
		are copied than the cells to paste, loop around copied items until
		paste cells are filled.
		'''
		i = 0
		n = len(self.copied)
		if n > 0:
			for it in self.selectedItems():
				if it == None:
					item = QTableWidgetItem(self.copied[i % n])
				else:
					it.setText(self.copied[i % n])
				i += 1

	def delete(self):
		'''
		Deletion without entering editing mode.
		'''
		for it in self.selectedItems():
			if it != None:
				it.setText('')
	
	def keyPressedEvent(evt):
		if evt.key() == Qt.Key_Delete:
			self.delete()
