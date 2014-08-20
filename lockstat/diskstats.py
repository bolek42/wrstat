# /proc/diskstats

import csv

import graphing

def parse( filename):
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
				"set title 'Sectors Reading/Writing %s'" % name,
				"set xlabel 'Runtime ( sec)'",
				"set ylabel 'Sectors/s'"]

		graphing.series( data, "%s/diskstats_sectors_%s_io.svg" % ( test_dir, name), "Sectors Reading/Writing %s" % name, cmds)
