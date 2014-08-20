#!/usr/bin/python
import os
import sys
import csv
import pickle

from utils import *

sample_rate = 1.0

## actual main ##
if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	sample_path = "%s/samples" % sys.argv[1]
	sample_file = "%s/samples.pickle" % sys.argv[1]

	#read config file
	config = load_config( "%s/lockstat.config" % sys.argv[1])
	sample_rate = float( config[ "samprate"])
	modules = load_modules( config[ "modules"])

	samples = {}
	for modname, module in modules.iteritems():
		data = module.parse( sys.argv[1])
		samples[ modname] = data

#		if ("diskstats_%d" % t) in files:
#			cont = True
#			if t == 0:
#				samples[ "diskstats"] = []
#			data = diskstats.parse( "%s/diskstats_%d" % ( sample_path, t))
#			samples[ "diskstats"].append( data)
#		if ("lock_stat_%d" % t) in files:
#			cont = True
#			if t == 0:
#				samples[ "lock_stat"] = []
#			data = lockstat.parse( "%s/lock_stat_%d" % ( sample_path, t))
#			samples[ "lock_stat"].append( data)
#		if ("stat_%d" % t) in files:
#			cont = True
#			if t == 0:
#				samples[ "stat"] = []
#			data = stat.parse( "%s/stat_%d" % ( sample_path, t))
#			samples[ "stat"].append( data)
#
#		t += 1
#
#	#end of ugly
#	if "oprofile" in files:
#		oprof = oprofile.parse( "%s/oprofile" % sample_path)
#		samples[ "oprofile"] = oprof
	
	f = open( sample_file, "w")
	pickle.dump( samples, f)
	f.close()
