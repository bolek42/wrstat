#!/usr/bin/python

import os
import sys
import csv
import numpy
import pylab
import operator
import pickle
import Gnuplot, Gnuplot.funcutils

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


def plot( usage, outfile, title, item):
	labels = []
	waittime= []

	for (class_name, lock_class) in sorted( usage.iteritems(), key=lambda (key, value): value[item]):
		labels.append( class_name)
		waittime.append( lock_class[item])

	bar_plot_stacked( outfile, title, waittime, labels, 0)

#term item
def plot_topn( samples, sample_rate, item, n, file, title):
	g = Gnuplot.Gnuplot( debug=0)
	g( "set terminal svg")
	g( "set output '%s'" % file)
	g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")

	g( "set title '%s'" % title)
	g( "set key outside")
	#g( "set key right top")
	g( "set key bottom right")
	g( "set key horizontal")
	#g( "set key reverse")
	g( "set key bmargin")
	g( "set xlabel 'runtime ( sec)'")
	g( "set ylabel 'percentage'")

	#determine top n
	top_names = []
	for key, value in samples[-1].iteritems():
		top_names.append( value)

	top_names = sorted( top_names, key=lambda x: x[item], reverse = True)
	
	#actual plot
	all = []
	plots = []
	for lock_class in top_names[0:n]:
		series = []
		for i in range( len( samples) - 1):
			if lock_class["name"] in samples[i]:
				t = ( samples[i+1][ lock_class["name"]][item] - 
					samples[i][ lock_class["name"]][item]   )
			else:
				t = 0.0

			series.append( (i / float( sample_rate), t / 1e4))

		plots.append( Gnuplot.PlotItems.Data( series, with_="lines", title=lock_class["name"]))

	g.plot( *plots)

#term item
def plot_topn_detailed( samples, sample_rate, sort_key, n, path):
	g = Gnuplot.Gnuplot( debug=0)
	g( "set terminal svg")

	#determine top n
	top_names = []
	for key, value in samples[-1].iteritems():
		top_names.append( value)

	top_names = sorted( top_names, key=lambda x: x[sort_key], reverse = True)
	
	#actual plot
	all = []
	for i in range( n):
		class_name = top_names[i]["name"]
		print class_name

		#calculating curves
		waittime = []
		contentions = []
		con_bounce = []
		for j in range( len( samples) - 1):
			if class_name in samples[j]:
				wt = ( samples[j+1][ class_name]["waittime-total"] - 
					samples[j][ class_name]["waittime-total"]   )

				ct = ( samples[j+1][ class_name]["contentions"] - 
					samples[j][ class_name]["contentions"]   )
				cb = ( samples[j+1][ class_name]["con-bounces"] - 
					samples[j][ class_name]["con-bounces"]   )

			else:
				wt = ct = cb = 0.0

			waittime.append( (j / float( sample_rate), wt / 1e4 * sample_rate))
			contentions.append( (j / float( sample_rate), ct * 100 * sample_rate))
			con_bounce.append( (j / float( sample_rate), cb * 100 * sample_rate))


		plots = []

		#plot
		g( "set output '%s/top-%d.svg'" % ( path, i))
		g( "clear")

		g( "set multiplot layout 2,2 title '%s'" % class_name)
		g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")


		g( "set title 'Waittime'")
		g.plot(Gnuplot.PlotItems.Data( waittime, with_="lines"))
		g("unset object 1")

		g( "set title 'Contentions - Bounces'")
		g( "set ylabel '#/s'")
		g( "set key bottom right")
		g( "set key outside")
		g( "set key bmargin")
		g( "set key horizontal")
		g.plot(	Gnuplot.PlotItems.Data( con_bounce, with_="lines", title="bounce"),
			Gnuplot.PlotItems.Data( contentions, with_="lines", title="cont.") )
		g( "set key default")

		g( "unset multiplot")

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	# load samples
	samples = []
	with open( "%s/samples" % sys.argv[1], 'r') as f:
		while 1:
			try: samples.append( pickle.load( f))
			except: break
	plot( samples[-1], "%s/waittime.svg" % sys.argv[1], "waittime total", "waittime-total")
	plot( samples[-1], "%s/holdtime.svg" % sys.argv[1], "holdtime total", "holdtime-total")

	plot_topn( samples, 2, "holdtime-total", 8, "%s/hold-time-sreies.svg" % sys.argv[1], "Total Hold Time")
	plot_topn_detailed( samples, 2, "waittime-total", 8, sys.argv[1])


