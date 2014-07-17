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
import shutil

path = ""
files = []
i = 0

def lockstat_capture():
	global i
	for src in files:
		dest = "%s/%s_%d" % ( path, src.replace( "/proc/", "").replace( "/", "_"), i)
		print "%s -> %s" % ( src, dest)
		shutil.copy( src, dest)
		os.chmod( dest, 6) # rwxrwxrwx = 000000110

	i += 1
	threading.Timer(0.5, lockstat_capture).start();

def signal_handler(signal, frame):
	print "captured signal " + str( signal)
	sample_file_mutex.acquire()
	sample_file.close()
        sys.exit(0)

if __name__ == "__main__":
	if len( sys.argv) < 3:
		print "usage: %s samplepath procfile1 procfile2 ..." % sys.argv[0]
		exit(1)

	path = sys.argv[1]
	for src in sys.argv[2:]:
		files.append( src)

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "capturing samples, use CTRL+C or SIGTERM to end"
	lockstat_capture()
