#/prpc/stat

import os
import csv

import graphing

name = "stat"

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

def stat_unit( u):
	return float( u) / os.sysconf_names['SC_CLK_TCK'] 

def parse_cpu_row( row):
	cpu = {}
	name = row[0]
	cpu[ "user"] = stat_unit( row[1])
	cpu[ "nice"] = stat_unit( row[2])
	cpu[ "system"] = stat_unit( row[3])
	cpu[ "idle"] = stat_unit( row[4])
	if len( row) > 5:
		cpu[ "iowait"] = stat_unit( row[5])
	if len( row) > 6:
		cpu[ "irq"] = stat_unit( row[6])
	if len( row) > 7:
		cpu[ "softirq"] = stat_unit( row[7])
	if len( row) > 8:
		cpu[ "steal"] = stat_unit( row[8])
	if len( row) > 9:
		cpu[ "guest"] = stat_unit( row[9])
	if len( row) > 10:
		cpu[ "guest_nice"] = stat_unit( row[10])

	return name, cpu
	
def parse( filename):
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
			stat[ row[ 0]] = stat_unit( row[1])
		# FIXME add missing

	stat["n_cpu"] = n_cpu
	return stat
