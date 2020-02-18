## Description
Whole-cell patch clamp recording results analysis program, including
some basic current clamp and voltage clamp analysis. It's used on 
data file collected using Igor.

## Installation
Could be installed through PyPl

```
pip install whole_cell_patch
```

or using source downloaded from here

```
python setup.py install
```

After installation the program could be launched in command line 
using command `whole_cell_patch`. It doesn't take arguments currently.

## Usage
### Data Organiaztion
The basic data management unit in this program is project. A project 
is composed of raw igor binary wave data files in one folder, and
a few analysis result files in another folder. The directory information
is saved in a project file for continuous analysis in separated
sessions. The analysis results are saved in separated files which are 
mostly csv files, with the intention that users could do further 
statistical analysis, which is not implemented in this program.
Besides data directory information, projects also manage which cells
would be analyzed, because sometimes the experimentors have reasons 
to exclude some cells. Within each cell, different trials might be
used to recorded different properties of cells using different protocols. 
This information could be specified so that further analysis could be 
applied to subsets of trials.
### Data visualization
This programms also allow users to plot wave data for examination or 
figure production.
### Analysis
Four common analysis methods were implemented in this program.

*   Action potentials recorded during contant current steps in 
    current clamp. Firing rate and action potential properties 
    will be analyzed.
*   Seal tests analysis, brief small subthreshold current/voltage
    steps used to test passive membrane properties.
*   Miniature postsynaptic response (abbriviated as minis) analysis. 
    This includes mini detection and property measurement.
*   Subthreshold response analysis. This is similar to seal test, 
    except that this is used in case of longer stimulations which 
    intend to characterize slower subthreshold properties such as 
    sag ratios.

These analysis usually involves a lot of user defined parameters. These
parameters could be exported to or imported from yaml files. Those files 
are independent from project files, in order to make parameter set 
reuse and sharing easier.

## Detailed Analysis Description
I'll write it later.

## TODO
1. <del>Trial selection based on stimulation for trace plot.</del>
2. Convenient cell selection input in analysis windows.
3. Display analysis module functions in the form of tabs to save space.
