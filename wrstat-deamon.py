#!/usr/bin/python
import sys
import signal
import threading
import time
import shutil
import csv

from utils import *

modules = []            #list of callable modules
sampling_threads = []   #list of sampling threads
cv = None               #condition variable used for thread synchronisation
t = 0                   #current sample
run = True              #True if deamon is running
test_dir = ""
_file = __file__


#The actual thread taking samples for a single module
def sample( module):
    global cv
    while run:
        module.sample( test_dir, t)

        cv.acquire()
        cv.wait()
        cv.release()


#timing thread which will wake up all threads at the specified intervall
def timer( intervall):
    global t
    global cv

    while run:
        #waking up all waiting samping threads
        cv.acquire()
        cv.notify_all()
        cv.release()

        time.sleep( intervall)
        t += 1


#catch a signal ( e.g. SIGINT) and shuts down the deamon
def signal_handler(signal, frame):
    global run

    print "%s: stopping all sampling threads..." % __file__
    run = False

    #wake up all waiting sampling threads for a clean exit
    finished = False
    while not finished:
        finished = True
        for t in sampling_threads:
            if t.is_alive():
                finished = False

        cv.acquire()
        cv.notify_all()
        cv.release()

    #deinitialize the modules
    for modname, module in modules.iteritems():
        print "%s: deinitialize %s" % ( _file, modname)
        module.postsampling( test_dir)

    #just to be safe, waiting for all threads to exit
    for thread in threading.enumerate():
        if thread != threading.current_thread():
            thread.join()


if __name__ == "__main__":
    if len( sys.argv) != 2:
        print "usage: %s test_dir" % sys.argv[0]
        exit(1)

    #read config file
    test_dir = sys.argv[1]
    config = load_config( "%s/wrstat.config" % test_dir)
    intervall = float( config[ "intervall"])
    modules = load_modules( config[ "modules"])

    print "%s: Making %.2f samples per second" % (__file__, 1.0/intervall)
    print "%s: starting deamon, use CTRL+C or SIGTERM to end" % __file__

    #initialize signalhandler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    #initialize modules by presampling method
    for modname, module in modules.iteritems():
            print "%s: initialize %s" % ( __file__, modname)
            module.presampling( test_dir)

    #signals wrstat to start the test command
    open( "%s/deamon.ready" % sys.argv[1], "w").close()

    #create sampling thread for each module
    cv = threading.Condition()
    for modname, module in modules.iteritems():
        thread = threading.Thread( target=sample, args=( module,))
        thread.start()
        sampling_threads.append( thread)

    timer( intervall)
