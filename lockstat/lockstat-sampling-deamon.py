#!/usr/bin/python
import sys
import signal
import threading
import shutil

files = []
sample_path = ""
i = 0

def capture():
	global i
	for src in files:
		try:
			dest = "%s/%s_%d" % ( path, src.replace( "/proc/", "").replace( "/", "_"), i)
			print "%s -> %s" % ( src, dest)
			shutil.copy( src, dest)
			os.chmod( dest, 0b000000110) # rwxrwxrwx = 000000110
		except:
			print "failed copy %s" % f

	i += 1

	threading.Timer(0.5, capture).start();

def signal_handler(signal, frame):
	print "captured signal " + str( signal)
	sys.exit(0)

if __name__ == "__main__":
	if len( sys.argv) < 3:
		print "usage: %s samplepath procfile1 procfile2 ..." % sys.argv[0]
		exit(1)

	sample_path = sys.argv[1]
	for src in sys.argv[2:]:
		files.append( src)

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "capturing samples, use CTRL+C or SIGTERM to end"
	capture()
