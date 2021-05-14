import os, math, datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.plotting import figure, gridplot, output_file, save

import argparse
parser = argparse.ArgumentParser(description='Command line arguments')
parser.add_argument("-i", "--inputfile", nargs='+', dest="filenames", default=["1/Hour1UnpackedData.csv"], help="Specify input files")
parser.add_argument("-o", "--outputfile", action="store", type=str, dest="outputfile", default="test.html", help="Specify output file")
parser.add_argument("-q", "--qtfile", nargs='+', dest="qtnames", default=["1/1QT1.csv"], help="Specify additional QT files")
parser.add_argument("-v", "--verbose", action="store", type=int, default=0, dest="verbose", help="Specify verbosity level")
args = parser.parse_args()

data_sampling = 1024 # data acquisition sampling frequency (in Hz)
plot_sampling = 100 # number of points per second to show (in Hz)
plot_ti = 3060 # Starting time for the plot (in s)
plot_tf = 3080 # End time for the plot (in s)
plot_range = 20 # range of the plots (in seconds)
tools_lits = "pan,wheel_zoom,box_zoom,reset,save,box_select,lasso_select"

inputFile = args.filenames[0]

columns = ['T', 'I', 'II', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
derivations = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']


df = pd.DataFrame()
qt = pd.DataFrame()

# Read file(s)
for filename in args.filenames:
	tdf = pd.read_csv(filename, names=columns, low_memory=False, skiprows=0) #nrows=args.max*1024 + 1 if args.max > 0 else 1e9,
	if args.verbose >= 1: print("Read %d lines from txt file %s" % (len(tdf), filename))
	df = df.append(tdf, ignore_index=True)
	df.reset_index(inplace=True, drop=True) # Reset indices to avoid repeated times

if args.verbose >= 0: print("Read file consisting of", len(df), "entries, corresponding to", datetime.timedelta(seconds=len(df)/1000.), "s")
if args.verbose >= 1: print(df.head(10))

# Read annotation file(s)
for qtname in args.qtnames:
    tqt = pd.read_csv(qtname, low_memory=False, skiprows=0)
    if args.verbose >= 1: print("Read %d lines from txt file %s" % (len(tqt), qtname))
    qt = qt.append(tqt, ignore_index=True)

if args.verbose >= 0: print("Read QT file consisting of", len(qt), "entries")
if args.verbose >= 1: print(qt.head(10))

times = len(df)/1000. # times are in milliseconds

# Derivations dataframe
df['TYPE'] = 0
df = df.astype({'TYPE' : "int32"})
#print(df.dtypes)

# Overwrite time with correct value
df['T'] = df.index / data_sampling

# Calculate missing derivations:
# III = II - I
# aVR = (-I - II) / 2
# aVL = (I - III) / 2
# aVF = (II + III) / 2
df['III'] = df['II'] - df['I']
df['aVR'] = (-df['I'] - df['II']) / 2.
df['aVL'] = (df['I'] - df['III']) / 2.
df['aVF'] = (df['II'] + df['III']) / 2.

df = df[['T', 'TYPE'] + derivations] # Reorder

if args.verbose >= 1: print(df.head(10))

# Annotations dataframe
qt['TYPE'] = 1

qt['T'] = qt['Time'] / data_sampling
qt = qt.astype({'TYPE' : "int32", 'Annotation': "int32"})
qt = qt[['T', 'TYPE', 'Annotation']] # FIXME

if args.verbose >= 1: print(qt[qt['Annotation'] != 0])

# Merge dataframes
md = pd.concat([df, qt])
md = md.sort_values(by=['T']).reset_index(drop=True)

if args.verbose >= 0: print("Saving output files")
df.to_csv("UnpackedData.csv")
qt.to_csv("Annotations.csv")
md.to_csv("MergedData.csv")


# ---------- Plot
if args.verbose >= 0: print("Plotting selected range")

dp = df.copy()
qp = qt.copy()

# For plotting, use only first 2 minutes
dp = dp[(dp['T'] >= plot_ti) & (dp['T'] < plot_tf)]
qp = qp[(qp['T'] >= plot_ti) & (qp['T'] < plot_tf)]

print("In the selected interval,", len(qp[qp['Annotation'] != 0]), "anomalous beats have been found")

# For plotting, consider only one row every N
dp = dp.iloc[::int(data_sampling/plot_sampling)]

# Output to static HTML file
output_file(args.outputfile)

figs = []

for der in derivations:
	fig = figure(width=1200, height=200, title="Derivazione " + der, x_axis_label="time (s)", y_axis_label="V (mV)", x_range=(plot_ti, plot_ti + plot_range), tools=['xpan', 'reset', 'save'])
	fig.line(dp['T'], dp[der], line_width=0.5)
	fig.sizing_mode = 'scale_width' # Scale plot width to page
	fig.inverted_triangle(qp.loc[qp['Annotation'] == 0, 'T'], np.tile( np.max(dp[der]), len(qp[qp['Annotation'] == 0])), line_color="green")
	fig.inverted_triangle(qp.loc[qp['Annotation'] != 0, 'T'], np.tile( np.max(dp[der]), len(qp[qp['Annotation'] != 0])), line_color="red")
	figs.append(fig)

# Link together the x-axes
for ide, der in enumerate(derivations): figs[ide].x_range = figs[0].x_range

# Put the subplots in a gridplot
p = gridplot([[x] for x in figs], toolbar_location=None)

# Show the results
save(p)

if args.verbose >= 0: print("Output saved to", args.outputfile)

# python3 plot.py -i 1/Hour*UnpackedData.csv -q 1/1QT*.csv -v 1
