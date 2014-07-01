#!/usr/bin/python

import os
import sys
import csv
import numpy
import pylab
import operator

colors = [ 	
		'#FF0000', '#00FF00', '#0000FF', 
		'#00FFFF', '#FF00FF', '#FFFF00', 
		'#880000', '#008800', '#000088', 
		'#008888', '#880088', '#888800', 
		'#0088FF', '#FF8800', '#88FF00',
		'#00FF88', '#88FF00', '#FF8800']

def  bar_plot_stacked( filename, title, data, labels, discarded):
	#convert data to range [0..yrange]
	max_entries = 16
	data = numpy.array( data)
	sum_all = data.sum( axis=0) + discarded
	data /= sum_all * ( 1 / 100.0)

	#actual ploting
	fig = pylab.figure()
	fig.clf()
	ax = pylab.subplot(111)
	ax.set_title( title)

	#plot others
	i = 0
	bottom = 0
	while i < len( data) - max_entries + 1 and i < len( data):
	#while ( i < len( data) - max_entries + 1 or data[i] < 0.5) and i < len( data):
		bottom += data[i]
		i += 1
	label = "(%2.2f%%) others" % bottom
	pylab.bar( 0, bottom, 1, color="#ffffff", label=label)

	#plot actual data
	while i < len( data):
		label = "(%2.2f%%) %s" % ( data[i], labels[i])
		pylab.bar( 0, data[i], 1, color=colors[i % len( colors)], bottom = bottom, label=label)
		bottom += data[i]
		i += 1

	#resize graph in x direction
	box = ax.get_position()
	ax.set_position([box.x0, box.y0, box.width * 0.3, box.height])

	#show labels in descending order
	handles, labels = ax.get_legend_handles_labels()
	ax.legend(handles[::-1], labels[::-1], loc='lower left', bbox_to_anchor=(1, 0))

	#disable xticks
	ax.get_xaxis().set_ticks([])
	ax.set_ylim([0, (sum_all - discarded) / sum_all * 100])

	#save file
	pylab.savefig( filename, tight_layout=True)

def plot_symbol_name( filename, title, rows, key, samples_discarded):
	rows = sorted( rows, key=lambda row: row[key])

	runtime = []
	labels = []
	for row in rows:
		runtime.append( float( row[key]))
		labels.append( row["symbol_name"])

	bar_plot_stacked( filename, title, runtime, labels, samples_discarded[key])

def lockstat_parse_usagerow( row):
	if len( row) < 11:
		print "invalid usage row"
		return None

	lockname = " ".join( row[ 0 : len( row) - 11 + 1])[0:-1]
	data = row[ len( row) - 11 + 1 ::]
	usage = {"name" : lockname,
		"lock" : [],
		"unlock" : [],
		"con-bounces" : int( data[0]),
		"contentions" : int( data[1]),
		"waittime-min" : float( data[2]),
		"waittime-max" : float( data[3]),
		"waittime-total" : float( data[4]),
		"acq-bounces" : int( data[5]),
		"acquisitions" : int( data[6]),
		"holdtime-min" : float( data[7]),
		"holdtime-max" : float( data[8]),
		"holdtime-total" : float( data[9])
		}
		
	return usage

def read_lockstat_lockrow( row):
	print row
	lock = { "con-bounces" : int( row[1]),
		"addr" : row[2],
		"symbol" : row[3]}

	return lock


def read_lockstat_data( filename):
	file = open( filename, "r")
	reader = csv.reader( file, delimiter=' ')
	rows = []
	for line in reader:
		data = []

		#strip whitespaces
		for element in line:
			if element != '':
				data.append( element)
		if len( data) > 0:
			rows.append( data)
	#discard version name and header
	rows = rows[ 4::]

	#FIXME
	usage = []
	i = 0
	state = "usage"
	for row in rows:
		if len(row) == 1 and row[0][0] == '-':
			if state == "usage":
				state = "lock"
			elif state == "lock":
				state = "unlock"
		elif len(row) == 1 and row[0][0] == '.':
			state = "usage"
		elif state == "usage":
			r = lockstat_parse_usagerow( row)
			if not( r is None):
				usage.append( r)
		elif state == "lock":
			lock = read_lockstat_lockrow( row)
		elif state == "unlock":
			lock = read_lockstat_lockrow( row)

		#print row
		#print state
		#print len( row)

	return usage

def plot( usage, outfile, title, key):
	labels = []
	waittime= []
	for usage in sorted( usage, key=lambda x: x[key]):
		labels.append( usage["name"])
		waittime.append( usage[key])

	bar_plot_stacked( outfile, title, waittime, labels, 0)

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	usage = read_lockstat_data( "%s/lock_stat" % sys.argv[1])

	plot( usage, "%s/waittime.svg" % sys.argv[1], "waittime total", "waittime-total")
	plot( usage, "%s/holdtime.svg" % sys.argv[1], "holdtime total", "holdtime-total")
