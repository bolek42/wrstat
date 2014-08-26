#!/usr/bin/python
import sys
import signal
import threading
import shutil
import csv

from utils import *

modules = []
t = 0
test_dir = ""
run = True

def capture():
	global t
	threads = []
	for modname, module in modules.iteritems():
		thread = threading.Thread( target=module.sample, args=( test_dir, t))
		thread.start()
		threads.append( thread)
	t += 1

	if run:
		threading.Timer( intervall, capture).start()

	for thread in threads:
		thread.join()

	#print "sample"

def signal_handler(signal, frame):
	#print "captured signal " + str( signal)

	print "captured %d samples" % t
	print "running postsampling..."
	for modname, module in modules.iteritems():
		module.postsampling( test_dir)

	#stopping sampling deamon
	global run
	run = False

	#waiting for all threads to exit
	for thread in threading.enumerate():
		if thread != threading.current_thread():
			thread.join()

if __name__ == "__main__":
	if len( sys.argv) != 2:
		print "usage: %s test_dir" % sys.argv[0]
		exit(1)


	#read config file
	config = load_config( "%s/lockstat.config" % sys.argv[1])
	intervall = float( config[ "intervall"])
	modules = load_modules( config[ "modules"])

	test_dir = sys.argv[1]

	print "sampling deamon: Making %f samples per second" % (1.0/intervall)

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	print "starting sampling deamon, use CTRL+C or SIGTERM to end"

	#starting capture
	for modname, module in modules.iteritems():
			module.presampling( test_dir)

	open( "%s/samplingdeamon.ready" % sys.argv[1], "w").close()
	capture()
