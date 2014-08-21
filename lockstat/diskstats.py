# /proc/diskstats
#TODO iostat

import os
import csv
import shutil

import graphing

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
	pass

def sample( test_dir, t):
	shutil.copy( "/proc/diskstats", "%s/samples/diskstats_%d" % ( test_dir, t))

def postsampling( test_dir):
	pass


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
	t = 0
	samples = []

	while os.path.isfile( "%s/samples/diskstats_%d" % ( test_dir, t)):
		sample = parse_sample( "%s/samples/diskstats_%d" % ( test_dir, t))
		samples.append( sample)

		t+= 1

	return samples

def parse_sample( filename):
	file = open( filename, "r")

	raw = list( csv.reader( file, delimiter=' '))
	#remove whitespaces and empty lines
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	devices = {}
	for row in rows:
		device = {}
		device[ "major-number"] = int( row[ 0])
		device[ "minor-number"] = int( row[ 1])
		device[ "device-name"] = row[ 2]
		device[ "reads-completed"] = int( row[ 3])
		device[ "reads-merger"] = int( row[ 4])
		device[ "sectors-read"] = int( row[ 5])
		device[ "time-read"] = int( row[ 6])
		device[ "writes-completed"] = int( row[ 7])
		device[ "writes-merger"] = int( row[ 8])
		device[ "sectors-write"] = int( row[ 9])
		device[ "time-write"] = int( row[ 10])
		device[ "in-progress"] = int( row[ 11])
		device[ "time-io"] = int( row[ 12])
		device[ "time-io-weighted"] = int( row[ 12])
		devices[ row[2]] = device
	file.close()

	return devices


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, samples, sample_rate):
	for name, device in samples[0].iteritems():
		#preparing data
		data = { "read" : [], "write" : []}
		sigma = 0.0
		for t in range( len( samples) - 1):
			read  = ( samples[t + 1][name]["sectors-read"] - 
				samples[t][name]["sectors-read"])
			write = ( samples[t + 1][name]["sectors-write"] -
				samples[t][name]["sectors-write"])
			sigma += read + write

			#normalize
			data[ "read"].append( ((t / sample_rate), read * sample_rate))
			data[ "write"].append( ((t / sample_rate), write * sample_rate))

		#determine if device has io throughput
		if sigma == 0:
			continue

		#create the plot
		title =  "/proc/diskstats Sectors Reading/Writing %s" % name
		filename = "%s/diskstats_sectors_%s_io.svg" % ( test_dir, name)
		g = graphing.init( title, filename)
		g( "set key outside")
		g( "set xlabel 'Runtime ( sec)'")
		g( "set ylabel 'Sectors/s'")
		graphing.series( data, g)
		g.close()
