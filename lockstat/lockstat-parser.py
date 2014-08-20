#!/usr/bin/python
import os
import sys
import csv
import pickle

#custom
import diskstats
import lockstat
import stat_foo as stat
import oprofile

sample_rate = 1.0

#TODO large try except blocks instead of if ;)
############## diskstats ##############

############## lockstat ##############

############## stat ##############

############## oprofile ##############


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
			data = diskstats.parse( "%s/diskstats_%d" % ( sample_path, t))
			samples[ "diskstats"].append( data)
		if ("lock_stat_%d" % t) in files:
			cont = True
			if t == 0:
				samples[ "lock_stat"] = []
			data = lockstat.parse( "%s/lock_stat_%d" % ( sample_path, t))
			samples[ "lock_stat"].append( data)
		if ("stat_%d" % t) in files:
			cont = True
			if t == 0:
				samples[ "stat"] = []
			data = stat.parse( "%s/stat_%d" % ( sample_path, t))
			samples[ "stat"].append( data)

		t += 1

	#end of ugly
	if "oprofile" in files:
		oprof = oprofile.parse( "%s/oprofile" % sample_path)
		samples[ "oprofile"] = oprof
	
	f = open( sample_file, "w")
	pickle.dump( samples, f)
	f.close()
