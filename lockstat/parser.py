import os
import sys
import csv
import numpy
import operator
import pickle

def lockstat_parse_lock_class( row):
	if len( row) < 11:
		print "invalid usage row"
		return None

	lockname = " ".join( row[ 0 : len( row) - 11 + 1])[0:-1]
	data = row[ len( row) - 11 + 1 ::]
	usage = {}
	usage[ "name"] = lockname,
	usage[ "read-locks"] = []
	usage[ "write-locks"] = []
	usage[ "con-bounces"] = int( data[0])
	usage[ "contentions"] = int( data[1])
	usage[ "waittime-min"] = float( data[2])
	usage[ "waittime-max"] = float( data[3])
	usage[ "waittime-total"] = float( data[4])
	usage[ "acq-bounces"] = int( data[5])
	usage[ "acquisitions"] = int( data[6])
	usage[ "holdtime-min"] = float( data[7])
	usage[ "holdtime-max"] = float( data[8])
	usage[ "holdtime-total"] = float( data[9])
		
	return usage

def lockstat_parse_lock( row):
	lock = {}
	lock[ "con-bounces"] = int( row[1])
	lock[ "addr"] = row[2]
	lock[ "symbol"] = row[3]

	return lock

def lockstat_read( filename):
	file = open( filename, "r")

	raw = list( csv.reader( file, delimiter=' '))
	raw = raw[ 4::] #discard version and header
	#remove whitespaces and empty lines
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	lock_classes = {}
	#to track the type of the current row we use a simple DFA
	state = "lock_class"
	for row in rows:
		if len( row) == 0:
			pass
		elif len(row) == 1 and row[0][0] == '-':
			if state == "lock_class":
				state = "read_lock" #FIXME inverse?
			elif state == "read_lock":
				state = "write_lock"

		elif len(row) == 1 and row[0][0] == '.':
			state = "lock_class"
		elif state == "lock_class":
			lock_class = lockstat_parse_lock_class( row)
			if not( lock_class is None):
				lock_classes.update( { lock_class["name"] : lock_class})
		elif state == "read_lock":
			lock = lockstat_parse_lock( row)
			if not( lock is None):
				lock_class["read-locks"].append( lock)
		elif state == "write_lock":
			lock = lockstat_parse_lock( row)
			if not( lock is None):
				lock_class["write-locks"].append( lock)

	file.close()
	return lock_classes

def diskstats_read( filename):
	file = open( filename, "r")

	raw = list( csv.reader( file, delimiter=' '))
	#remove whitespaces and empty lines
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	devices = {}
	#to track the type of the current row we use a simple DFA
	state = "lock_class"
	for row in rows:
		device = {}
		device[ "major-number"] = int( row[ 0])
		device[ "minor-number"] = int( row[ 1])
		device[ "device-name"] = row[ 2]
		device[ "reads-completed"] = int( row[ 3])
		device[ "reads-merger"] = int( row[ 4])
		device[ "sectors-read"] = int( row[ 5])
		device[ "time-reading"] = int( row[ 6])
		device[ "writes-completed"] = int( row[ 7])
		device[ "writes-merger"] = int( row[ 8])
		device[ "sectors-written"] = int( row[ 9])
		device[ "time-write"] = int( row[ 10])
		device[ "in-progress"] = int( row[ 11])
		device[ "time-io"] = int( row[ 12])
		device[ "time-io-weighted"] = int( row[ 12])
		devices[ row[2]] = {}
	file.close()

	return devices

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	lock_stat = {}
	diskstats = {}
	test_dir = sys.argv[1]
	for file in os.listdir( "%s/samples/" % test_dir):
		filename = "%s/samples/%s" % ( test_dir,file)
		if os.path.isfile( filename):
			if file.replace( "lock_stat_", "").isdigit():
				t = int( file.replace( "lock_stat_", ""))
				lock_stat[ t] = lockstat_read( filename)
			if file.replace( "diskstats_", "").isdigit():
				t = int( file.replace( "diskstats_", ""))
				diskstats[ t] = lockstat_read( filename)
			print os.path.join( file)

	samples = { "lock_stat" : [], "diskstats" : []}
	for i in range( len(lock_stat)):
		samples[ "lock_stat"].append( lock_stat[i])

	for i in range( len(diskstats)):
		samples[ "diskstats"].append( diskstats[i])

	print samples
	f = open( "%s/samples.pickle" % sys.argv[1], "w")
	pickle.dump( samples, f)
	f.close()
