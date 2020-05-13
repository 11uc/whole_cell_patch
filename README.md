## Description
Whole-cell patch clamp recording results analysis program, including
some basic current clamp and voltage clamp analysis. It's used on 
data file collected using a Igor program made by a previous lab member.
The files are in the format of igor binary wave files (.ibw). Those files
include metadata such as time and stimulation information. 

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
applied to subsets of trials recorded with different protocols. Protocols
could be specified by trials numbers or stimulation type, which is in
the meta information of the raw data.
### Data visualization
This programms also allow users to plot wave data for examination or 
figure production.
### Analysis
Four common analysis methods were implemented in this program.

*   Action potentials recorded during contant current steps in 
    current clamp. Firing rate, action potential properties and
	rheobase will be analyzed.
*   Seal tests analysis, brief small subthreshold current/voltage
    steps used to test passive membrane properties.
*   Miniature postsynaptic response (abbriviated as minis) analysis. 
    This includes mini detection and property measurement.
*   Subthreshold response analysis. This is similar to seal test, 
    except that this is used in case of longer stimulations which 
    intend to characterize slower subthreshold properties such as 
    sag ratios.

A module to plot raw data traces, averaged or not, is also implemented
as an analysis module.

These analysis usually involves a lot of user defined parameters. These
parameters could be exported to or imported from yaml files. Those files 
are independent from project files, in order to make parameter set 
reuse and sharing easier.
### Process
Premilinary process applied to the traces before being analyzed or 
plotted. Currently only basic filters are implemented.
### Example
Here's an example procedure to analyze some mini recording data.

*	Go to **Project -> Edit project** and specify experiment name, working 
	directory (an empty folder for output data), raw data folders.
*	(optional) Go to **Project -> Select cells** and specify cells to include.
*	Go to **Project -> Assign protocol** and assign protocols to trials.
*	(optional) Go to **Project -> Assign cell** types to label cell groups.
*	Go to **File -> Save project** to save project information edited above.
*	(optional) Specify cell and trial number and click **Display** to examine 
	raw traces.
*	Go to **Analysis -> Mini analysis**. Under Mini Analysis tab, specify 
	protocol and click **Go** to detect minis. Set verbose to 1 to see the 
	progress.
*	Under Properties tab, specify protocol, cells. Click **Go** to output mini 
	properties data in a csv file in working directory. If seal tests are done
	for those trial, RinTh and numTh could be specified to exclude trials/cells
	with too high access resistance.

## Detailed Analysis Description
### Action potential
This module takes input traces recorded in current clamp firing in 
response to constant current steps of different levels. The amplitude 
of the stimulation steps should be in the metadata.
#### Basic parameters
*	*spike_slope_threshold*: slope threshold to detect action potential 
	spikes, V/s. The higher the harder for a peak to be qualified.
*	*spike_peak_threshold*: peak ampiltide, relative to the point where
	the slope cross the threshold. for action potential spike, V. The
	higher the harder for a peak to be qualified.
*	*half_width_threshold*: maximum half height width for the peak, s.
*	*sign*: sign of peak relative to baseline, 1 for postive and -1 for
	negative.
*	*mAHP_begin*: latency of time window of mAHP relative to start of 
	action potentials, mAHP amplitude is averaged over the window between
	*mAHP_begin* and *mAHP_end*.
*	*baseline*: time ahead of current stimulation to calculate baseline
	amplitude from.
*	*sAHP_begin*: latency of time window of sAHP relative to the end of 
	current stimulation, sAHP amplitude is averaged over the window between
	*sAHP_begin* and *sAHP_end*.
#### Spike Detect
*	*verbose*: level of details to display during calculation.  
	0 - nothing.  
	1 - display cell and trial numbers.  
	2 - display each dected spike for parameter tuning.
#### Firing Rate
Calculate average firing rate for each cell with each stimulation current
over trials.

*	*cells*: ids of cells for which to calculate firing rate. Leave empty
	to include all cells.
*	*stims*: amplitude of current stimulation for which to calculate, A.
	Leave empty to include all stimulations.
#### Properties
Calculate average properties of action potentials for cells.

*	*cells*: ids of cells for which to calculate the properties. Leave empty
	to include all cells.
*	*rateRange*: firing rate a trial to have to be included. Leave the
	same to include all firing rate.
*	*idRange*: ids which a action potential in a trial to have to be included.
	Leave the same to include all action potentials.
#### Accommondation
Calculate average accomondation ratio of instantaneous firing rate between two 
action potentials. It's define as the second action potential over the first
action potential.

*	*cells*: ids of cells for which to calculate the properties. Leave empty
	to include all cells.
*	*rateRange*: firing rate a trial to have to be included. Leave the
	same to include all firing rate.
*	*early_ap*: id of the first action potential.
*	*late_ap*: id of the second action potential
#### Rheobase
Calculate average rheobases for cells, i.e. the least amount current required
for the neuron to fire action potentials.

*	*cells*: ids of cells for which to calculate. Leave empty to include all 
	cells.
### Seal test
Calculate passive membrane properties of cells from seal tests, step the
current or voltage by a little amount. The membrane capacitor charging is
assumed to be an exponential decay for the calculation.
#### Basic parameters
*	*baseline_start*, *baseline_end*: start/end of baseline time window, s.
*	*steady_state_start*, *steady_state_end*: start/end of steady state time 
	window, s.
*	*seal_test_start*: start time point of the voltage/current step, s.
*	*fit_end*: end time point for the exponential fit, s.
*	*scale_V*: by which the amplitude is scaled up in voltage clamp for better
	fitting.
*	*scale_I*: by which the amplitude is scaled up in current clamp for better
	fitting.
*	*ampV*: voltage clamp test step amplitude, V.
*	*ampI*: current clamp test step amplitude, A.
*	*minTau*: minimum time constant of the exponential decay for the results
	to be accepted, s. Below this, an error will be reported.
#### Seal Test
Calculate the passive properties using seal tests.

*	*comp*: whether the input resistance is compensated during recordring. If
	so, won't attempt to calculate it.
*	*clamp*: voltage (v) or current (i) clamp.
*	*verbose*: level of details to display during calculation.  
	0 - nothing.  
	1 - display cell and trial numbers.  
	2 - display fitting result for each trial.
#### Properties
Output the averaged passive properties of selected *cells*.
### Mini analysis
Detect miniature postsynaptic currents/potentials, minis, and calculate their
properties. The peaks are fitted to a function in the form of the sum of
two exponetial functions, one positive and one negative.
#### Basic parameters
*	*sign*: sign of the minis relative to the baseline.
*	*medianFilterWinSize*: number of points for median filter to remove single
	ponit noises. The median filter is usually not necessary.
*	*medianFilterThresh*: amplitude of the median filter, same unit as the raw
	trace data.
*	*lowBandWidth*: frequency threshold for low band pass filter to smooth the
	raw data.
*	*riseSlope*: threshold of peak rise slope. Peaks with rise slope above
	which will be included.
*	*riseTime*: time threshold of peak rise, s. Time to rise to peak need to be
	below this threshold.
*	*baseLineWin*: time window size to calculate baseline amplitude from, s.
*	*minAmp*: peak amplitude threshold. Peak amplitude need to be above this.
*	*minTau*: time constant threshold, s. The time constant of the negative
	expoential function need to be above this value.
*	*residual*: residual threshold. The residual from the least square regression 
	need to be below this.
*	*onTauIni*: initialize value for the time constant of the positive expoential
	function.
*	*offTauIni*: initialize value for the time constant of the negative expoential
	function.
*	*stackWin*: distance threshold for consecutive peaks, s. Two minis that 
	are stacked needs to be separated by a time above this value to be considered
	two minis.
*	*scale*: scale value for better fitting.
#### Mini Analysis
Detecting minis.

*	*win*: time window in which the minis will be detected.
*	*verbose*: level of details to display during detection.  
	0 - nothing.  
	1 - display cell and trial numbers.  
	2 - display detection result for each trial.
	3 - display fitting result for each mini.
#### Properties
Output averaged mini properties.

*	*cells*: ids of cells for which to calculate. Leave empty to include all 
	cells.
*	*RinTh*: input resistance threshold, &Omega. Trials with input resistance
	below this value will be included. Not applied if left as 0.
*	*numTh*: number of trials below Rin threshold threshold. Cells with more
	trials included than this number are included.
### Subthreshold response analysis
Analyze subthreshold stimulation step responses. Similar to seal test, except
that this usually includes stimulations of a series of amplitudes.
#### Basic parameters
*	*baseline_start*, *baseline_end*: start/end of baseline time window relative
	to the start of the stimulation, s.
*	*steady_state_start*, *steady_state_end*: start/end of steady state time 
	window relative to the start of the stimulation, s.
*	*fit_start*, *fit_end*: start/end time point for the exponential fit 
	relative to the start of stimulation, s.
*	*scale_V*: by which the amplitude is scaled up in voltage clamp for better
	fitting.
*	*scale_I*: by which the amplitude is scaled up in current clamp for better
	fitting.
*	*minTau*: minimum time constant of the exponential decay for the results
	to be accepted, s. Below this, an error will be reported.
#### Subthreshold
Calculate passive subthreshold properties.

*	*comp*: whether the input resistance is compensated during recordring. If
	so, won't attempt to calculate it.
*	*clamp*: voltage (v) or current (i) clamp.
*	*verbose*: level of details to display during calculation.  
	0 - nothing.  
	1 - display cell and trial numbers.  
	2 - display fitting result for each trial.
#### Properties
Output averaged passive properties for *cells* over trials with stimulation of
amplitudes within *stimRange*.
#### IV
Output current-voltage data for amplitudes of stimulation and response.

*	*win*: steady state window to calculate the response amplitude, relative to
	the stimulation start, s.
*	*baseWin*: baseline window for calculate baseline amplitude, relative to
	the stimulation start, s.
*	*method*: the way the amplitude is calculated in the response window.  
	mean - average  
	min - minumum value  
	max - maximum value  
*	*cells*: ids of cells for which to calculate. Leave empty to include all 
	cells.
*	*verbose*: level of details to display during calculation.  
	0 - nothing.  
	1 - display cell and trial numbers.  
#### Substraction
Calculate response amplitude difference to the same stimulation of two protocols
and output the IV data.

*	*cells*: ids of cells for which to calculate. Leave empty to include all 
	cells.
*	*stims*: amplitude of stimulation for which to calculate.  Leave empty to
	include all stimulations.
*	*toPlot*: whether to generage the difference amplitude plots.
*	*hanging*: window to include before and after the stimulation in the
	difference plot.
### Multiple trace plot
Plot averaged raw data traces.

*	*types*: types of cells to be included, leave empty to include all.
*	*cells*: ids of cells to be includedd, leave empty to include all.
*	*stims*: amplitudes of trials to be includedd, leave empty to include all.
*	*trials*: id of trials to be includedd, leave empty to include all.
*	*aveLevel*: at which level to average the traces.
	none - plot each trial separately.
	trials - average over trials in the same cell with the same stimulations.
	cells - average over cells of the same type.
*	*label1*, *label2*: whether/how to label the traces by color, combination
	of two labels is allowed. Label by cell, trial, stim or type or don't label
	(none).
*	*normWin*: baseline window to normalize the traces to before averaging. 
	Normalization won't be applied if it's left the same.
*	*win*: window within which the trace will be plotted. The entire trace will
	be plotted if it's left the same.
*	*errorBar*: whether to plot error bar when averaged.
*	*magnify*: times to magnify to plot to include more details.

## TODO
1. <del>Trial selection based on stimulation for trace plot.</del>
2. Convenient cell selection input in analysis windows.
3. <del>Display analysis module functions in the form of tabs to save space.</del>
