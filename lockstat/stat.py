#/prpc/stat

import os
import csv
import shutil

import graphing

def unit( u):
	return float( u) / os.sysconf_names['SC_CLK_TCK'] 

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
	pass

def sample( test_dir, t):
	shutil.copy( "/proc/stat", "%s/samples/stat_%d" % ( test_dir, t))

def postsampling( test_dir):
	pass


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
	t = 0
	samples = []

	while os.path.isfile( "%s/samples/stat_%d" % ( test_dir, t)):
		sample = parse_sample( "%s/samples/stat_%d" % ( test_dir, t))
		samples.append( sample)

		t+= 1

	return samples

def parse_sample( filename):
	file = open( filename, "r")

	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	stat = {}

	n_cpu = -1
	for row in rows:
		if row[0][0:3] == "cpu":
			name, cpu = parse_cpu_row( row)
			stat[ name] = cpu
			n_cpu += 1
		elif len( row) == 2:
			stat[ row[ 0]] = unit( row[1])
		#TODO add missing

	stat["n_cpu"] = n_cpu
	return stat


def parse_cpu_row( row):
	cpu = {}
	name = row[0]
	cpu[ "user"] = unit( row[1])
	cpu[ "nice"] = unit( row[2])
	cpu[ "system"] = unit( row[3])
	cpu[ "idle"] = unit( row[4])
	if len( row) > 5:
		cpu[ "iowait"] = unit( row[5])
	if len( row) > 6:
		cpu[ "irq"] = unit( row[6])
	if len( row) > 7:
		cpu[ "softirq"] = unit( row[7])
	if len( row) > 8:
		cpu[ "steal"] = unit( row[8])
	if len( row) > 9:
		cpu[ "guest"] = unit( row[9])
	if len( row) > 10:
		cpu[ "guest_nice"] = unit( row[10])

	return name, cpu


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, stat, sample_rate):
	#aggregate sampled
	plot_stat_series( stat, "cpu", "%s/stat_aggreagted_sampled.svg" % test_dir, "Stat aggreagted sampled", sample_rate)

	#per cpu aggregated
	data = {}
	for key, value in stat[0]["cpu"].iteritems():
		data[ key] = []

	for cpu in range( stat[0]["n_cpu"]):
		for key, value in data.iteritems():
			value.append( stat[-1]["cpu%d" % cpu][key] - stat[0]["cpu%d" % cpu][key])

		#per cpu sampled
		plot_stat_series( stat, "cpu%d" % cpu, "%s/stat_cpu%d_sampled.svg" % ( test_dir, cpu), "Stat CPU %d sampled" % cpu, sample_rate)
	

	#aggregated
	cmds = [ "set xrange [-0.5:%.1f]" % (stat[0]["n_cpu"] - 0.5),
			"set xlabel 'CPU'"]
	graphing.histogram( data, "%s/stat_percpu.svg" % test_dir, "Stat per CPU", cmds)

def plot_stat_series( stat, cpu, filename, title, sample_rate):
	data = {}
	for key, value in stat[0][cpu].iteritems():
		data[ key] = []

	for t in range( len( stat) - 1):
		for key, value in data.iteritems():
			value.append( ( t / sample_rate, stat[t + 1][cpu][key] - stat[t][cpu][key]))

	cmds = [	"set key outside",
			"set key bottom right",
			"set key horizontal",
			"set key bmargin",
			"set xlabel 'runtime ( sec)'",
			"set ylabel 'Runtime %'"]
	graphing.series( data, filename, title, cmds)

