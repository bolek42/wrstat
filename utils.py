import os
import imp
import csv
import Queue
import threading

def load_config( filename):
    #read samplerate from config
    file = open( filename, "r")
    raw = list( csv.reader( file, delimiter=' '))
    rows = map( lambda row: filter(lambda s: s != '', row), raw)

    config = {}
    for row in rows:
        if len( row) == 1:
            config[ row[0]] = []
        if len( row) == 2:
            config[ row[0]] = row[ 1:][0]
        elif len( row) > 2:
            config[ row[0]] = row[ 1:]

    return config

def load_modules( modnames, mod_dir):
    if isinstance( modnames, basestring):
        modnames = [ modnames]

    modules = {}
    for modname in modnames:
        try:
            modules[ modname] =  imp.load_source( modname, "%s/%s.py" % ( mod_dir, modname))
        except:
            print "error loading %s" % modname
            raise

    return modules

def get_tool_path():
    return os.path.dirname( os.path.realpath( __file__))

def log(data, filename):
    f = open(filename, "a")
    f.write(data+"\n")
    f.close()

#this methods implement a queued copy in an extra thread
#the queue used is thread safe
#this is the actual method that can be used for copy
#files will be read immediately queued for writing
def copy_queued( src, dest):
    global copy_queue
    global copy_cv


    f = open( src, "r")
    data = f.read()
    f.close()

    if not copy_run:
        print "error: copy thread not running, writing directly!"
        f = open( dest, "w")
        f.write( data)
        f.close()
        return

    #put data
    copy_queue.put( (dest, data))

    #notify copy thread
    copy_cv.acquire()
    copy_cv.notify_all()
    copy_cv.release()

############################################
#this methods will be called by wrstat only#
############################################
copy_queue = None
copy_run = False
copy_cv = None
copy_thread = None

#the actual thread, that will write the data to disk
def copy_queued_worker():
    global copy_queue
    global copy_cv

    while copy_run or not copy_queue.empty():
        #unqueue and write files
        while not copy_queue.empty():
            dest, data = copy_queue.get()

            f = open( dest, "w")
            f.write( data)
            f.close()

        #wait for data
        if copy_run:
            copy_cv.acquire()
            copy_cv.wait()
            copy_cv.release()


def copy_queued_init():
    global copy_queue
    global copy_run
    global copy_cv
    global copy_thread

    copy_queue = Queue.Queue()
    copy_run = True
    copy_cv = threading.Condition()
    copy_thread = threading.Thread( target=copy_queued_worker)
    copy_thread.start()


def copy_queued_finish():
    global copy_run
    global copy_cv

    #end thread
    copy_run = False
    copy_cv.acquire()
    copy_cv.notify_all()
    copy_cv.release()
    copy_thread.join()

