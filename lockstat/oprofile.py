#oprofile
import csv
import operator
import shutil

import graphing

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
	pass

def sample( test_dir, t):
	pass

def postsampling( test_dir):
	pass


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
	#read and sanitize data
	file = open( "%s/samples/oprofile" % test_dir, "r")
	raw = csv.reader( file, delimiter=' ')
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	n_cpu = 0
	data = []
	for row in rows:
		#skip header rows
		if len( row) < 4 or not row[0].isdigit():
			continue

		if n_cpu == 0:
			n_cpu = (len ( row) / 2) - 1

		#process fields
		line = dict()
		samples_aggregate = 0.0
		runtime_aggregate = 0.0
		for cpu in range( n_cpu):
			sample = int( row[cpu * 2])
			runtime = float( row[(cpu * 2) + 1])
			line[ "samples_cpu%d" % cpu] = sample
			line[ "runtime_cpu%d" % cpu] = runtime
			samples_aggregate += sample
			runtime_aggregate += runtime		

		line[ "samples_aggregate"] = samples_aggregate
		line[ "runtime_aggregate"] = runtime_aggregate
		line[ "app_name"] = row[ -2]
		line[ "symbol_name"] = row[ -1]

		data.append( line)

	oprof = {}
	oprof[ "rows"] = data
	oprof[ "n_cpu"] = n_cpu

	return oprof #returns n_cpu and data


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, data, sample_rate):
	n_cpu = data[ "n_cpu"]
	rows = data[ "rows"]
	#separate plot 
	for cpu in range( n_cpu):
		plot_histogram( "%s/cpu_%d" % (test_dir, cpu), rows, "samples_cpu%d" % cpu, "Total Runtime CPU %d" % cpu, 0)

	plot_histogram( "%s/cpu_aggregate" % test_dir, rows, "samples_aggregate", "Total Runtime Aggregate", 0)

def plot_histogram( prefix, rows, key, title_prefix, discarded):
	rows = sorted( rows, key=lambda row: row[key])
	data = {}
	for row in rows:
		data[ row["symbol_name"]] = [float( row[key])]

	cmds = [ "unset xtics"]
	graphing.histogram_percentage( data, "%s_sym.svg" % prefix, "%s (Symbol Names)" % title_prefix, discarded)

	apps = {}
	for row in rows:
		if row["app_name"] not in apps:
			apps[ row["app_name"]] = 0.0

		apps[row["app_name"]] += row[key]

	data = {}
	for app, usage in sorted( apps.iteritems(), key=operator.itemgetter(1)):
		data[ app] = [float( usage)]

	graphing.histogram_percentage( data, "%s_app.svg" % prefix, "%s (App Names)" % title_prefix, discarded)
