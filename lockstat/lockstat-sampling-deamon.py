#!/usr/bin/python

import os
import sys
import csv
import numpy
import operator
import pickle
import signal
import thread
import threading

def lockstat_parse_lock_class( row):
	if len( row) < 11:
		print "invalid usage row"
		return None

	lockname = " ".join( row[ 0 : len( row) - 11 + 1])[0:-1]
	data = row[ len( row) - 11 + 1 ::]
	usage = {"name" : lockname,
		"read-locks" : [],
		"write-locks" : [],
		"con-bounces" : int( data[0]),
		"contentions" : int( data[1]),
		"waittime-min" : float( data[2]),
		"waittime-max" : float( data[3]),
		"waittime-total" : float( data[4]),
		"acq-bounces" : int( data[5]),
		"acquisitions" : int( data[6]),
		"holdtime-min" : float( data[7]),
		"holdtime-max" : float( data[8]),
		"holdtime-total" : float( data[9])
		}
		
	return usage

def lockstat_parse_lock( row):
	lock = { "con-bounces" : int( row[1]),
		"addr" : row[2],
		"symbol" : row[3]}

	return lock

#TODO parser offloading
#FIXME DFA with string comparison
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

def lockstat_capture():
	sample_file_mutex.acquire()
	threading.Timer(0.5, lockstat_capture).start();

	print "sample"
	# If you want to make file I/O more efficient, reimplement in C
	pickle.dump( lockstat_read( "/proc/lock_stat"), sample_file)
	sample_file.flush()
	sample_file_mutex.release()

def signal_handler(signal, frame):
	print "captured signal " + str( signal)
	sample_file_mutex.acquire()
	sample_file.close()
        sys.exit(0)

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s samplefile" % sys.argv[0]
		exit(1)

	sample_file = open( sys.argv[1], "w")
	sample_file_mutex = thread.allocate_lock()

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "capturing samples, use CTRL+C or SIGTERM to end"
	lockstat_capture()
