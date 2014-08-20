#!/usr/bin/python

import os
import sys
import csv
import operator
import pickle

sample_rate = 1.0

import imp

def load_config( filename): 
	#read samplerate from config
	file = open( filename, "r")
	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	config = {}
	for row in rows:
		config[ row[0]] = row[ 1:]

	return config

def load_modules( modnames):
	modules = {}
	for modname in modnames:
		modules[ modname] =  imp.load_source( modname, "%s.py" % modname)

	return modules

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir oprofile_filter1 ...(filtering not implemented)" % sys.argv[0]
		exit(1)

	#read samplerate from config
	config = load_config( "%s/lockstat.config" % sys.argv[1])
	sample_rate = float( config[ "samprate"][0])
	modules = load_modules( config[ "modules"])

	# load samples
	f = open( "%s/samples.pickle" % sys.argv[1], 'r')
	samples = pickle.load( f)

	for modname, module in modules.iteritems():
		if modname in samples:
			module.plot( sys.argv[1], samples[modname], sample_rate)
			
