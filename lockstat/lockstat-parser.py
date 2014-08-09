#!/usr/bin/python
import os
import re
import sys
import csv
import pickle

sample_rate = 1.0

#TODO large try except blocks instead of if ;)
############## diskstats ##############
def diskstats_read( filename):
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

############## lockstat ##############
def lockstat_parse_lock_class( row, keys):
	if len( row) <= len( keys):
		print "invalid usage row"
		return None

	lockname = row[ 0 : len( row) - len( keys)]
	lockname = " ".join( lockname)
	lockname = lockname[0:-1]

	data = row[ len( row) - len( keys) ::]

	usage = {}
	usage[ "name"] = lockname
	usage[ "read-locks"] = []
	usage[ "write-locks"] = []

	for key, value in zip(keys, data):
		usage[ key] = float( value)
		
	return usage

def lockstat_parse_lock( row, offset):
	lock = {}
	lock[ "con-bounces"] = int( row[offset])
	lock[ "addr"] = row[offset + 1]
	lock[ "symbol"] = row[offset + 2]

	return lock

def lockstat_read( filename):
	file = open( filename, "r")

	raw = list( csv.reader( file, delimiter=' '))
	#remove whitespaces and empty
	raw = map( lambda row: filter(lambda s: s != '', row), raw)
	#lines discard version and header
	rows = raw[ 4::] 

	#read keys from header line
	keys = []
	for k in raw[2][2:]:
		keys.append( k)

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
			lock_class = lockstat_parse_lock_class( row, keys)
			if not( lock_class is None):
				lock_classes.update( { lock_class["name"] : lock_class})
		elif state == "read_lock":
			name_offset = lock_class["name"].count( ' ')  + 1
			lock = lockstat_parse_lock( row, name_offset)
			if not( lock is None):
				lock_class["read-locks"].append( lock)
		elif state == "write_lock":
			name_offset = lock_class["name"].count( ' ')  + 1
			lock = lockstat_parse_lock( row, name_offset)
			if not( lock is None):
				lock_class["write-locks"].append( lock)

	file.close()
	return lock_classes

############## stat ##############
def stat_unit( u):
	return float( u) / os.sysconf_names['SC_CLK_TCK'] 

def stat_cpurow( row):
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
	
def stat_read( filename):
	file = open( filename, "r")

	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	stat = {}

	n_cpu = -1
	for row in rows:
		if row[0][0:3] == "cpu":
			name, cpu = stat_cpurow( row)
			stat[ name] = cpu
			n_cpu += 1
		elif len( row) == 2:
			stat[ row[ 0]] = stat_unit( row[1])
		# FIXME add missing

	stat["n_cpu"] = n_cpu
	return stat

############## oprofile ##############
def read_oprofile( filename):
	file = open( filename, "r")
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


## actual main ##
if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	sample_path = "%s/samples" % sys.argv[1]
	sample_file = "%s/samples.pickle" % sys.argv[1]

	#read samplerate from config
	file = open( "%s/lockstat.config" % sys.argv[1], "r")
	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)
	for row in rows:
		if row[0].lower() == "samprate":
			sample_rate = float( row[1])

	#FIXME ugly
	files = []
	for f in os.listdir( sample_path):
		files.append( f)

	t = 0
	samples = {}
	cont = True
	while cont:
		cont = False
		if ("diskstats_%d" % t) in files:
			cont = True
			if t == 0:
				samples[ "diskstats"] = []
			samples[ "diskstats"].append( diskstats_read( "%s/diskstats_%d" % ( sample_path, t)))
		if ("lock_stat_%d" % t) in files:
			cont = True
			if t == 0:
				samples[ "lock_stat"] = []
			samples[ "lock_stat"].append( lockstat_read( "%s/lock_stat_%d" % ( sample_path, t)))
		if ("stat_%d" % t) in files:
			cont = True
			if t == 0:
				samples[ "stat"] = []
			samples[ "stat"].append( stat_read( "%s/stat_%d" % ( sample_path, t)))

		t += 1
	#end of ugly
	if "oprofile" in files:
		oprof = read_oprofile( "%s/oprofile" % sample_path)
		samples[ "oprofile"] = oprof
	
	f = open( sample_file, "w")
	pickle.dump( samples, f)
	f.close()
