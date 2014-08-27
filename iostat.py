import os
import subprocess

import graphing
from utils import *

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
	subprocess.call( [ "./iostat-init.sh", test_dir])

def sample( test_dir, t):
	pass

def postsampling( test_dir):
	subprocess.call( [ "./iostat-deinit.sh", test_dir])


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
	file = open( "%s/iostat" % test_dir, "r")
	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	samples = []
	for row in rows[1:]:
		if len( row) == 0:
			continue

		if row[0] == "Device:":
			sample = {}
			samples.append( sample)
		else:
			device = {}
			device[ "tps"] = float( row[ 1])
			device[ "read"] = float( row[ 2])
			device[ "write"] = float( row[ 3])
			sample[ row[0]] = device


	return samples



#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, data, intervall):
	#prepare data
	read = {}
	write = {}
	for sample in data:
		for name, device in sample.iteritems():
			if name not in read:
				read[ name] = []
				write[ name] = []
			read[ name].append( device[ "read"] / 1024.0)
			write[ name].append( device[ "write"] / 1024.0)
		

	#all disks reading
	title =  "iostat all Reading"
	filename = "%s/iostat-read.svg" % test_dir
	g = graphing.init( title, filename)
	g( "set key outside")
	g( "set xlabel 'Runtime ( sec)'")
	g( "set ylabel 'MiB/s'")
	graphing.series( read, g)
	g.close()

	#all disks writing
	title =  "iostat all Writing"
	filename = "%s/iostat-write.svg" % test_dir
	g = graphing.init( title, filename)
	g( "set key outside")
	g( "set xlabel 'Runtime ( sec)'")
	g( "set ylabel 'MiB/s'")
	graphing.series( write, g)
	g.close()

	#per device graph
	for name, device in data[0].iteritems():
		title =  "iostat %s Reading/Writing" % name
		filename = "%s/iostat-%s-write.svg" % ( test_dir, name)
		g = graphing.init( title, filename)
		g( "set key outside")
		g( "set xlabel 'Runtime ( sec)'")
		g( "set ylabel 'MiB/s'")
		graphing.series( {"read" : read[ name], "write" : write[ name]}, g)
		g.close()
		
