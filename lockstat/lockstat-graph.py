#!/usr/bin/python

import os
import sys
import csv
import operator
import pickle

#custom
import diskstats
import lockstat
import stat_foo as stat
from graphing import * #FIXME
import oprofile

sample_rate = 1.0

### oprofile ###

### lockstat ###

#term item

### stat ###

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir oprofile_filter1 ...(filtering not implemented)" % sys.argv[0]
		exit(1)

	#read samplerate from config
	file = open( "%s/lockstat.config" % sys.argv[1], "r")
	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)
	for row in rows:
		if row[0].lower() == "samprate":
			sample_rate = float( row[1])

	# load samples
	f = open( "%s/samples.pickle" % sys.argv[1], 'r')
	samples = pickle.load( f)

	if "lock_stat" in samples:
		lockstat.plot( sys.argv[1], samples["lock_stat"], sample_rate)
	if "diskstats" in samples:
		diskstats.plot( sys.argv[1], samples["diskstats"], sample_rate)
	if "stat" in samples:
		stat.plot( sys.argv[1], samples["stat"], sample_rate)
	if "oprofile" in samples:
		oprofile.plot( sys.argv[1], samples["oprofile"], sample_rate)
