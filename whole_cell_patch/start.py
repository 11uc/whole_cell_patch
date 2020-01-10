# Start the gui

import sys
from PyQt5.QtWidgets import QApplication
from .main import wcpMainWindow

def start_gui():
	app = QApplication(sys.argv)
	mainWindow = wcpMainWindow()
	sys.exit(app.exec_())
