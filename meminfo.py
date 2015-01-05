# /proc/meminfo

import os
import csv
import shutil
import  subprocess

import graphing
from utils import *

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
    pass

def sample( test_dir, t):
    if os.path.isfile( "/proc/meminfo"):
        copy_queued( "/proc/meminfo", "%s/samples/meminfo_%d" % ( test_dir, t))

def postsampling( test_dir):
    pass


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
    t = 0
    samples = []

    while os.path.isfile( "%s/samples/meminfo_%d" % ( test_dir, t)):
        sample = parse_sample( "%s/samples/meminfo_%d" % ( test_dir, t))
        samples.append( sample)

        t+= 1

    return samples

def parse_sample( filename):
    file = open( filename, "r")

    raw = list( csv.reader( file, delimiter=' '))
    #remove whitespaces and empty lines
    rows = map( lambda row: filter(lambda s: s != '', row), raw)

    sample = {}
    for row in rows:
        key = row[0][:-1]
        sample[key] = int( row[1])
    file.close()

    return sample


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, samples, intervall):
    if len( samples) < 1:
        print "%s nothing captured" % __file__
        return

    keys = [ "MemTotal", "MemAvailable", "MemFree", "Cached",  "SwapTotal", "SwapFree"]
    graph = {}
    for key in samples[0]:
        avg = 0.0
        n = 0.0
        timeseries = []
        for t in range( len( samples) - 1):
            #convert to MiB
            value = int(samples[t][key]) / 1024.0
            timeseries.append( ((t * intervall), value))
            avg += value
            n += 1

        avg /= n
        if "Swap" in key:
            print key
            print timeseries
            print avg

        if key in keys:
            title = "%s (%d MiB)" % (key, avg)
            graph[title] = timeseries
            log( "Meminfo averge %s: \t %.2f MiB" % (key, avg), "%s/stat.txt" % test_dir)

    log( "", "%s/stat.txt" % test_dir)

    #plotting
    title =  "/proc/meminfo"
    filename = "%s/meminfo.svg" % test_dir

    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set key bottom right")
    g( "set key horizontal")
    g( "set key bmargin")
    g( "set xlabel 'Runtime ( sec)'")
    g( "set ylabel 'MiB'")
    graphing.series( graph, g)
    g.close()

