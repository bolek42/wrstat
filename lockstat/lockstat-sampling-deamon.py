#!/usr/bin/python
import os
import sys
import csv
import numpy
import operator
import pickle
import signal
import threading
import shutil

files = []
t = 0
sample_path = ""

def capture():
	global t
	for f in files:
		try:
			print "%s" % f
			shutil.copy( f, "%s/%s_%d" % ( sample_path, f.split('/')[-1], t))
		except:
			print "failed copy %s" % f

	t += 1
	print "sample"

	threading.Timer(0.5, capture).start();

def signal_handler(signal, frame):
	print "captured signal " + str( signal)
	sys.exit(0)

if __name__ == "__main__":
	if len( sys.argv) < 3:
		print "usage: %s sample_path file1 file2 ..." % sys.argv[0]
		exit(1)

	sample_path = sys.argv[1]
	for f in sys.argv[2:]:
		files.append( f)

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "capturing samples, use CTRL+C or SIGTERM to end"
	capture()
