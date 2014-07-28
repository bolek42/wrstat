#!/usr/bin/python
import sys
import signal
import threading
import shutil
import csv

files = []
path = ""
t = 0
sample_rate = 1.0

#FIXME buffering because of diskio lags
def capture():
	global t
	snapshot = {}
	for src in files:
		try:
			dest = "%s/%s_%d" % ( path, src.replace( "/proc/", "").replace( "/", "_"), t)
			print "sampling deamon: loading %s" % src
			f = open( src, "r")
			snapshot[ dest] = f.read()
			f.close()
		except:
			print "sampling deamon: failed to load %s" % src
	t += 1

	threading.Timer( 1.0/sample_rate, capture).start()

	for dest, data in snapshot.iteritems():
		print "sampling-deamon: writing %s" % dest
		f = open( dest, "w")
		f.write( str( data))
		f.close()

def signal_handler(signal, frame):
	print "captured signal " + str( signal)
	sys.exit(0)

if __name__ == "__main__":
	if len( sys.argv) < 3:
		print "usage: %s test_dir procfile1 procfile2 ..." % sys.argv[0]
		exit(1)

	#read samplerate from config
	file = open( "%s/lockstat.config" % sys.argv[1], "r")
	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)
	for row in rows:
		if row[0].lower() == "samprate":
			sample_rate = float( row[1])

	print "sampling deamon: Making %d samples per second" % sample_rate

	path = "%s/samples" % sys.argv[1]
	for src in sys.argv[2:]:
		files.append( src)

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "sampling deamon: capturing samples, use CTRL+C or SIGTERM to end"
	capture()
