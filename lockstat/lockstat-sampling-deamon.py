#!/usr/bin/python
import sys
import signal
import threading
import shutil
import csv

from utils import *

modules = []
t = 0
sample_rate = 1.0
test_dir = ""

def capture():
	global t
	global modules
	global test_dir

	threads = []
	for modname, module in modules.iteritems():
		thread = threading.Thread( target=module.sample, args=( test_dir, t))
		thread.start()
		threads.append( thread)
	t += 1

	threading.Timer( 1.0/sample_rate, capture).start()

	for thread in threads:
		thread.join()

	print "sample"


def signal_handler(signal, frame):
	print "captured signal " + str( signal)

	print "running postcapture..."
	for modname, module in modules.iteritems():
		module.postsampling( test_dir)

	sys.exit(0)

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)

	#read config file
	config = load_config( "%s/lockstat.config" % sys.argv[1])
	sample_rate = float( config[ "samprate"])
	modules = load_modules( config[ "modules"])

	test_dir = sys.argv[1]

	print "sampling deamon: Making %d samples per second" % sample_rate

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "starting sampling deamon, use CTRL+C or SIGTERM to end"

	#starting capture

	for modname, module in modules.iteritems():
		module.presampling( test_dir)

	capture()
