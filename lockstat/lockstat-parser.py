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

	sample_file = "%s/samples.pickle" % sys.argv[1]

	#read config file
	config = load_config( "%s/lockstat.config" % sys.argv[1])
	sample_rate = float( config[ "samprate"])
	modules = load_modules( config[ "modules"])

	#calling modules for parsing
	samples = {}
	for modname, module in modules.iteritems():
		data = module.parse( sys.argv[1])
		samples[ modname] = data
	
	f = open( sample_file, "w")
	pickle.dump( samples, f)
	f.close()
