# /proc/diskstats

import os
import csv
import shutil

import graphing

def presampling( test_dir):
	pass

def sample( test_dir, t):
	shutil.copy( "/proc/diskstats", "%s/samples/diskstats_%d" % ( test_dir, t))

def postsampling( test_dir):
	pass

#TODO iostat
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

def parse( test_dir):
	t = 0
	samples = []

	while os.path.isfile( "%s/samples/diskstats_%d" % ( test_dir, t)):
		sample = parse_sample( "%s/samples/diskstats_%d" % ( test_dir, t))
		samples.append( sample)

		t+= 1

	return samples

def plot( test_dir, diskstats, sample_rate):
	#aggregate sampled

	#FIXME remove this when time is the last dimension!
	names = []
	for name, device in diskstats[0].iteritems():
		if device[ "sectors-read"] + device[ "sectors-write"] > 0:
			names.append( name)

	for name in names:
		data = { "read" : [], "write" : []}
		for t in range( len( diskstats) - 1):
			read  = diskstats[t + 1][name]["sectors-read"] - diskstats[t][name]["sectors-read"]
			write = diskstats[t + 1][name]["sectors-write"] - diskstats[t][name]["sectors-write"]

			#normalize
			data[ "read"].append( ((t / sample_rate), read * sample_rate))
			data[ "write"].append( ((t / sample_rate), write * sample_rate))

		cmds = [	"set key outside",
				"set xlabel 'Runtime ( sec)'",
				"set ylabel 'Sectors/s'"]

		graphing.series( data, "%s/diskstats_sectors_%s_io.svg" % ( test_dir, name), "Sectors Reading/Writing %s" % name, cmds)
