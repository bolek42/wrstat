#!/usr/bin/python

import os
import sys
import csv
import numpy
import pylab
import operator
import pickle

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

	samples = []
	with open( "%s/samples" % sys.argv[1], 'r') as f:
		samples.append( pickle.load( f))

	plot( samples[-1], "%s/waittime.svg" % sys.argv[1], "waittime total", "waittime-total")
	plot( samples[-1], "%s/holdtime.svg" % sys.argv[1], "holdtime total", "holdtime-total")
