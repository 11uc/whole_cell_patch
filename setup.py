# Set up the whole_cell_patch package.

from setuptools import setup

def readme():
	with open("README.md") as f:
		return f.read()

setup(name = "whole_cell_patch",
      version = '0.1',
      description = ("Analysis scripts used to analyze whole-cell "
		  "patch clamp recording data."),
      url = "https://github.com/11uc/whole_cell_patch",
      author = "Chenghao Liu",
      author_email = "liuc@brandeis.edu",
      license = "MIT",
      packages = ["whole_cell_patch"],
	  install_requires = [
		  "PyQt5",
		  "numpy >= 1.17.3",
		  "pandas >= 0.25.2",
		  "pyqtgraph == 0.10.0",
		  "scipy >= 1.3.1",
		  "PyYAML >= 5.1.2",
		  "igor >= 0.3"],
	  entry_points = {
		  "gui_scripts": [
			  "whole_cell_patch = whole_cell_patch.start:start_gui"]},
      zip_safe = False,
	  python_requires = ">=3.7",
	  classifiers = [
		  "Development Status :: 3 - Alpha",
		  "License :: OSI Approved :: MIT License",
		  "Programming Language :: Python :: 3.7"]
	  )
