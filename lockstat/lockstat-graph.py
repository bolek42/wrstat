#!/usr/bin/python

import os
import sys
import csv
import numpy
#import pylab
import operator
import pickle
import Gnuplot, Gnuplot.funcutils

sample_rate = 2
colors = [ 	
		'#FF0000', '#00FF00', '#0000FF', 
		'#00FFFF', '#FF00FF', '#FFFF00', 
		'#880000', '#008800', '#000088', 
		'#008888', '#880088', '#888800', 
		'#0088FF', '#FF8800', '#88FF00',
		'#00FF88', '#88FF00', '#FF8800']

#term item
def plot_series( data, file, cmds, g = Gnuplot.Gnuplot( debug=0)):
	g( "set terminal svg")
	g( "set output '%s'" % file)
	g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")

	for cmd in cmds:
		g( cmd)

	plots = []
	for name, series in data.iteritems():
		plots.append( Gnuplot.PlotItems.Data( series, with_="lines", title=str(name)))

	g.plot( *plots)

#term item
def plot_topn_detailed( samples, sample_rate, sort_key, n, path):
	#determine top n
	top_names = []
	for key, value in samples[-1].iteritems():
		top_names.append( value)

	top_names = sorted( top_names, key=lambda x: x[sort_key], reverse = True)
	
	#actual plot
	all = []
	for i in range( n):
		class_name = top_names[i]["name"]

		#calculating curves
		waittime = []
		contentions = []
		con_bounce = []
		acquisitions = []
		for j in range( len( samples) - 1):
			if class_name in samples[j]:
				wt = ( samples[j+1][ class_name]["waittime-total"] - 
					samples[j][ class_name]["waittime-total"]   )

				aq = ( samples[j+1][ class_name]["acquisitions"] - 
					samples[j][ class_name]["acquisitions"]   )
				ct = ( samples[j+1][ class_name]["contentions"] - 
					samples[j][ class_name]["contentions"]   )
				cb = ( samples[j+1][ class_name]["con-bounces"] - 
					samples[j][ class_name]["con-bounces"]   )

			else:
				wt = aq = ct = cb = 0.0

			waittime.append( (j / float( sample_rate), wt * sample_rate))
			acquisitions.append( (j / float( sample_rate), aq * sample_rate))
			contentions.append( (j / float( sample_rate), ct * sample_rate))
			con_bounce.append( (j / float( sample_rate), cb * sample_rate))

		histogram = []
		#FIXME term read_locks
		for lock in samples[-1][ class_name]["read-locks"]:
			data = Gnuplot.PlotItems.Data( [lock["con-bounces"]], title="%s ( write)"
				% (lock[ "symbol"]))
			histogram.append( data)

		for lock in samples[-1][ class_name]["write-locks"]:
			data = Gnuplot.PlotItems.Data( [lock["con-bounces"]], title="%s ( read)"
				% (lock[ "symbol"]))
			histogram.append( data)


		#plot
		g = Gnuplot.Gnuplot( debug=0)
		g( "reset")
		g( "set terminal svg")
		g( "set output '%s/top-%d.svg'" % ( path, i))

		#g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")
		g( "set multiplot title '%s'" % class_name)


		g( "set title 'Waittime'")
		g( "set ylabel 'wait us/s'")
		g( "set origin 0,0.45")
		g( "set size 0.5,0.5")
		g.plot(Gnuplot.PlotItems.Data( waittime, with_="lines"))
		#g("unset object 1")

		g( "set title 'Acquisitions - Contentions'")
		g( "set ylabel '#/s'")
		g( "set key bottom right")
		g( "set logscale y")
		g( "set key outside")
		g( "set key bmargin")
		g( "set key horizontal")
		g( "set origin 0.5,0.45")
		g( "set size 0.5,0.5")
		g.plot(	Gnuplot.PlotItems.Data( acquisitions, with_="lines", title="acqu."),
			Gnuplot.PlotItems.Data( contentions, with_="lines", title="cont.") )
#		g.plot(	Gnuplot.PlotItems.Data( waittime_per_bounce, with_="lines"))
		g( "unset logscale y")
		g( "set key default")

		#histogram
		g( "unset xtics")
		g( "set ylabel 'Bounces Total'")
		g( "set title 'Bounces - Functions'")
		g( "set style data histograms")
		g( "set style histogram rowstacked")
		g( "set style fill solid border -1")
		g( "set key invert reverse Left outside")
		g( "set origin 0,0")
		g( "set size 1,0.5")
		g.plot(	*histogram)

		g.close()

def plot_histogram( data, filename, title):
	histogram = []
	for key, value in data.iteritems():
		pl = Gnuplot.PlotItems.Data( value, title=str( key))
		histogram.append( pl)

	#histogram
	g = Gnuplot.Gnuplot( debug=0)
	g( "reset")
	g( "set terminal svg")
	g( "set output '%s'" % filename)
	g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")
	g( "set yrange [0:100]")
	g( "set ylabel 'Runtime Percentage'")
	g( "set title '%s'" % title)
	g( "set style data histograms")
	g( "set style histogram rowstacked")
	g( "set style fill solid border -1")
	g( "set key invert reverse Left outside")
	g.plot(	*histogram)

	g.close()

def plot_histogram_percentage( data, filename, title, discarded):
	histogram = []

	sigma = float( discarded)
	for key, value in data.iteritems():
		sigma += value

	others = 100.0
	for key, value in sorted( data.iteritems(), key=lambda (key, value): value, reverse=True)[0:16]:
		percentage = value * 100.0 / sigma
		others -= percentage
		pl = Gnuplot.PlotItems.Data( [ percentage], title=("%s (%.2f%%)" % (str( key), percentage)))
		histogram.append( pl)
	if others > 0.0:
		pl = Gnuplot.PlotItems.Data( [ others], title=("others (%.2f%%)" % percentage))
		histogram.append( pl)
	histogram.reverse()

	#histogram
	g = Gnuplot.Gnuplot( debug=0)
	g( "reset")
	g( "set terminal svg")
	g( "set output '%s'" % filename)
	g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")
	g( "set yrange [0:100]")
	g( "set ylabel 'Runtime Percentage'")
	g( "set title '%s'" % title)
	g( "set style data histograms")
	g( "set style histogram rowstacked")
	g( "set style fill solid border -1")
	g( "set key invert reverse Left outside")
	g.plot(	*histogram)

	g.close()

def plot_oprofile_percentage( prefix, rows, key, title_prefix, discarded):
	rows = sorted( rows, key=lambda row: row[key])

	data = {}
	for row in rows:
		data[ row["symbol_name"]] = float( row[key])

	plot_histogram_percentage( data, "%s_sym.svg" % prefix, "%s (Symbol Names)" % title_prefix, discarded)

	apps = {}
	for row in rows:
		if row["app_name"] not in apps:
			apps[ row["app_name"]] = 0.0

		apps[row["app_name"]] += row[key]

	data = {}
	for app, usage in sorted( apps.iteritems(), key=operator.itemgetter(1)):
		data[ app] = float( usage)

	plot_histogram_percentage( data, "%s_app.svg" % prefix, "%s (App Names)" % title_prefix, discarded)

def plot_oprofile( test_dir, data):
	n_cpu = data[ "n_cpu"]
	rows = data[ "rows"]
	#separate plot 
	for cpu in range( n_cpu):
		plot_oprofile_percentage( "%s/cpu_%d" % (test_dir, cpu), rows, "samples_cpu%d" % cpu, "Total Runtime CPU %d" % cpu, 0)

	plot_oprofile_percentage( "%s/cpu_aggregate" % test_dir, rows, "samples_aggregate", "Total Runtime Aggregate", 0)

def plot_lock_stat( test_dir, samples):
	data = {}
	for (class_name, lock_class) in samples[-1].iteritems():
		data[ class_name] = lock_class[ "waittime-total"]
	plot_histogram_percentage( data, "%s/lockstat_waititme.svg" % test_dir, "Waittime Total", 0)

	data = {}
	for (class_name, lock_class) in samples[-1].iteritems():
		data[ class_name] = lock_class[ "holdtime-total"]
	plot_histogram_percentage( data, "%s/lockstat_holdtime.svg" % test_dir, "Waittime Total", 0)

	#plot_topn( samples, 2, "holdtime-total", 8, "%s/hold-time-sreies.svg" % sys.argv[1], "Total Hold Time")
	#determine top n
	top_names = []
	for key, value in samples[-1].iteritems():
		top_names.append( value)

	top_names = sorted( top_names, key=lambda x: x["waittime-total"], reverse = True)
	
	#actual plot
	data = {}
	for lock_class in top_names[0:8]:
		series = []
		for i in range( len( samples) - 1):
			if lock_class["name"] in samples[i]:
				t = ( samples[i+1][ lock_class["name"]]["waittime-total"] - 
					samples[i][ lock_class["name"]]["waittime-total"]   )
			else:
				t = 0.0

			series.append( (i / float( sample_rate), t))

		data[ lock_class["name"]] = series

	cmds = [	"set key outside",
			"set title 'Waittime Top'",
			"set key bottom right",
			"set key horizontal",
			"set key bmargin",
			"set xlabel 'runtime ( sec)'",
			"set ylabel 'usec/s'"]

	plot_series( data, "%s/lockstat_waittime_top.svg" % test_dir, cmds)
	plot_topn_detailed( samples, 2, "waittime-total", 8, sys.argv[1])

def plot_stat( test_dir, stat):
	#aggregate sampled
	data = { "user" : [], "nice" : [], "system" : [], "idle" : []}

	for t in range( len( stat) - 1):
		user = stat[t + 1]["cpu"]["user"] - stat[t]["cpu"]["user"]
		nice = stat[t + 1]["cpu"]["nice"] - stat[t]["cpu"]["nice"]
		system = stat[t + 1]["cpu"]["system"] - stat[t]["cpu"]["system"]
		idle = stat[t + 1]["cpu"]["idle"] - stat[t]["cpu"]["idle"]

		#normalize
		total = float( user + nice + system + idle)
		data[ "user"].append( user / total * 100)
		data[ "nice"].append( nice / total * 100)
		data[ "system"].append( system / total * 100)
		data[ "idle"].append( idle / total * 100)

	plot_histogram( data, "%s/stat_aggreagted_sampled.svg" % test_dir, "stat aggreagted sampled")

	#per cpu
	data = { "user" : [], "nice" : [], "system" : [], "idle" : []}
	for cpu in range( stat[0]["n_cpu"]):
		user = stat[-1]["cpu%d" % cpu]["user"] - stat[0]["cpu%d" % cpu]["user"]
		nice = stat[-1]["cpu%d" % cpu]["nice"] - stat[0]["cpu%d" % cpu]["nice"]
		system = stat[-1]["cpu%d" % cpu]["system"] - stat[0]["cpu%d" % cpu]["system"]
		idle = stat[-1]["cpu%d" % cpu]["idle"] - stat[0]["cpu%d" % cpu]["idle"]

		#normalize
		total = float( user + nice + system + idle)
		data[ "user"].append( user / total * 100)
		data[ "nice"].append( nice / total * 100)
		data[ "system"].append( system / total * 100)
		data[ "idle"].append( idle / total * 100)

	plot_histogram( data, "%s/stat_percpu.svg" % test_dir, "stat per cpu")

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	# load samples
	f = open( "%s/samples.pickle" % sys.argv[1], 'r')
	samples = pickle.load( f)

	if "lock_stat" in samples:
		plot_lock_stat( sys.argv[1], samples["lock_stat"])
	if "stat" in samples:
		plot_stat( sys.argv[1], samples["stat"])
	if "oprofile" in samples:
		plot_oprofile( sys.argv[1], samples["oprofile"])
