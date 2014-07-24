#!/usr/bin/python
import sys
import signal
import threading
import shutil

files = []
path = ""
i = 0

#FIXME buffering because of diskio lags
def capture():
	global i
	snapshot = {}
	for src in files:
		try:
			dest = "%s/%s_%d" % ( path, src.replace( "/proc/", "").replace( "/", "_"), i)
			print "loading %s" % src
			f = open( src, "r")
			snapshot[ dest] = f.read()
			f.close()
		except:
			print "failed copy %s" % src
	i += 1

	threading.Timer(0.5, capture).start();

	for dest, data in snapshot.iteritems():
		print "writing %s" % dest
		f = open( dest, "w")
		f.write( str( data))
		f.close()

def signal_handler(signal, frame):
	print "captured signal " + str( signal)
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
	capture()
