#!/usr/bin/python

import sys
import pickle

from utils import *

sample_rate = 1.0

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir oprofile_filter1 ...(filtering not implemented)" % sys.argv[0]
		exit(1)

	#read samplerate from config
	config = load_config( "%s/lockstat.config" % sys.argv[1])
	sample_rate = float( config[ "samprate"])
	modules = load_modules( config[ "modules"])

	# load samples
	f = open( "%s/samples.pickle" % sys.argv[1], 'r')
	samples = pickle.load( f)

	for modname, module in modules.iteritems():
		if modname in samples:
			module.plot( sys.argv[1], samples[modname], sample_rate)
			
