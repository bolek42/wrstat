#oprofile
import os
import csv
import shutil
import operator
import subprocess

import graphing

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
	print "to run oprofile, root access is required"
	subprocess.call( [ "sudo", "./oprofile-init.sh", test_dir])

def sample( test_dir, t):
	pass

def postsampling( test_dir):
	subprocess.call( [ "sudo", "./oprofile-deinit.sh", test_dir])


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
	if not os.path.isfile( "%s/samples/oprofile" % test_dir):
		return None

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

		#determine number of cpus
		if n_cpu == 0:
			n_cpu = (len ( row) / 2) - 1

		#process fields for each row
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

#FIXME term rows
def plot( test_dir, data, intervall):
	if data is None:
		return

	n_cpu = data[ "n_cpu"]
	rows = data[ "rows"]
	#separate plot 
	for cpu in range( n_cpu):
		file_prefix = "%s/oprofile-cpu%d" % (test_dir, cpu)
		title_prefix = "Total Runtime CPU %d" % cpu
		plot_histogram( file_prefix, rows, "samples_cpu%d" % cpu, title_prefix, 0)

	#aggregated plot
	file_prefix = "%s/oprofile-aggregate" % test_dir
	title_prefix = "Total Runtime Aggregate"
	plot_histogram( file_prefix, rows, "samples_aggregate", title_prefix, 0)

def plot_histogram( file_prefix, rows, key, title_prefix, discarded):
	rows = sorted( rows, key=lambda row: row[key])

	#prepare data for symbol names
	data = {}
	for row in rows:
		data[ row["symbol_name"]] = [float( row[key])]

	#actual plotting
	title = "Oprofile %s (Symbol Names)" % title_prefix
	filename = "%s_sym.svg" % file_prefix
	g = graphing.init( title, filename)
	graphing.histogram_percentage( data, discarded, g)
	g.close()

	#prepare data for app names
	apps = {}
	for row in rows:
		if row["app_name"] not in apps:
			apps[ row["app_name"]] = 0.0

		apps[row["app_name"]] += row[key]

	data = {}
	for app, usage in sorted( apps.iteritems(), key=operator.itemgetter(1)):
		data[ app] = [float( usage)]

	#actual plotting
	title = "Oprofile %s (App Names)" % title_prefix
	filename = "%s_app.svg" % file_prefix
	g = graphing.init( title, filename)
	graphing.histogram_percentage( data, discarded, g)
	g.close()
