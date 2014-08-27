# /proc/diskstats
#TODO iostat

import os
import csv
import shutil
import  subprocess

import graphing
from utils import *

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
	subprocess.call( [ "./diskstats-init.sh", test_dir])

def sample( test_dir, t):
	if os.path.isfile( "/proc/diskstats"):
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

	blocksize = parse_blocksize( test_dir)

	return {"samples" : samples, "blocksize" : blocksize}

def parse_blocksize( test_dir):
	blocksize = load_config( "%s/blocksizes" % test_dir)

	for name, bs in blocksize.iteritems():
		blocksize[ name] = int( bs)

	return blocksize

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

def plot( test_dir, data, intervall):

	samples = data[ "samples"]
	for name, device in samples[0].iteritems():
		phy_name = name
		while phy_name not in data[ "blocksize"]:
			phy_name = phy_name[:-1]
		blocksize = data[ "blocksize"][phy_name]

		#preparing data
		sectors = { "read" : [], "write" : []}
		time = { "read" : [], "write" : []}
		sigma = 0.0
		for t in range( len( samples) - 1):
			read  = ( samples[t + 1][name]["sectors-read"] - 
				samples[t][name]["sectors-read"])
			write = ( samples[t + 1][name]["sectors-write"] -
				samples[t][name]["sectors-write"])
			read *= blocksize
			write *= blocksize

			sigma += read + write

			#normalize
			sectors[ "read"].append( ((t * intervall), read * intervall))
			sectors[ "write"].append( ((t * intervall), write * intervall))

			time_read = ( samples[t + 1][name]["time-read"] -
				samples[t][name]["time-read"])
			time_write = ( samples[t + 1][name]["time-write"] -
				samples[t][name]["time-write"])

			#normalize
			time[ "read"].append( ((t * intervall), time_read * intervall))
			time[ "write"].append( ((t * intervall), time_write * intervall))

		#determine if device has io throughput
		if sigma == 0:
			continue

		#plotting sectors/s
		title =  "/proc/diskstats Sectors Reading/Writing %s" % name
		filename = "%s/diskstats-%s-sectors.svg" % ( test_dir, name)
		g = graphing.init( title, filename)
		g( "set key outside")
		g( "set xlabel 'Runtime ( sec)'")
		g( "set ylabel 'Sectors/s'")
		graphing.series( sectors, g)
		g.close()

		#plotting time spent on io
		title =  "/proc/diskstats Time spent on IO %s" % name
		filename = "%s/diskstats-%s-time-io.svg" % ( test_dir, name)
		g = graphing.init( title, filename)
		g( "set key outside")
		g( "set xlabel 'Runtime ( sec)'")
		g( "set ylabel 'ms/s'")
		graphing.series( time, g)
		g.close()
