# /proc/diskstats
#TODO iostat

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
    tool_path = get_tool_path()
    subprocess.call( [ "%s/diskstats-init.sh" % tool_path, test_dir])

def sample( test_dir, t):
    if os.path.isfile( "/proc/diskstats"):
        copy_queued( "/proc/diskstats", "%s/samples/diskstats_%d" % ( test_dir, t))

def postsampling( test_dir):
    pass


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
    t = 0
    samples = []

    while os.path.isfile( "%s/samples/diskstats_%d" % ( test_dir, t)):
        sample = parse_sample( "%s/samples/diskstats_%d" % ( test_dir, t))
        samples.append( sample)

        t+= 1

    sectorsize = parse_sectorsize( test_dir)

    return {"samples" : samples, "sectorsize" : sectorsize}

def parse_sectorsize( test_dir):
    sectorsize = load_config( "%s/sectorsizes" % test_dir)

    for name, bs in sectorsize.iteritems():
        sectorsize[ name] = int( bs)

    return sectorsize

def parse_sample( filename):
    file = open( filename, "r")

    raw = list( csv.reader( file, delimiter=' '))
    #remove whitespaces and empty lines
    rows = map( lambda row: filter(lambda s: s != '', row), raw)

    devices = {}
    for row in rows:
        device = {}
        device[ "major-number"] = int( row[ 0])
        device[ "minor-number"] = int( row[ 1])
        device[ "device-name"] = row[ 2]
        device[ "reads-completed"] = int( row[ 3])
        device[ "reads-merger"] = int( row[ 4])
        device[ "sectors-read"] = int( row[ 5])
        device[ "time-read"] = int( row[ 6])
        device[ "writes-completed"] = int( row[ 7])
        device[ "writes-merger"] = int( row[ 8])
        device[ "sectors-write"] = int( row[ 9])
        device[ "time-write"] = int( row[ 10])
        device[ "in-progress"] = int( row[ 11])
        device[ "time-io"] = int( row[ 12])
        device[ "time-io-weighted"] = int( row[ 12])
        devices[ row[2]] = device
    file.close()

    return devices


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, data, intervall):
    samples = data[ "samples"]
    if len( samples) < 2:
        print "%s nothing captured" % __file__
        return

    io_read = {}
    io_write = {}
    time_read = {}
    time_write = {}
    for name, device in samples[0].iteritems():
        phy_name = name
        while phy_name not in data[ "sectorsize"]:
            phy_name = phy_name[:-1]
        sectorsize = data[ "sectorsize"][phy_name]

        #preparing data
        io = { "read" : [], "write" : []}
        time = { "read" : [], "write" : []}
        sigma = 0.0
        for t in range( len( samples) - 1):
            read  = ( samples[t + 1][name]["sectors-read"] -
                samples[t][name]["sectors-read"])
            write = ( samples[t + 1][name]["sectors-write"] -
                samples[t][name]["sectors-write"])
            #convert to MiB/s
            read *= sectorsize / 1048576.0
            write *= sectorsize / 1048576.0

            sigma += read + write

            #normalize
            io[ "read"].append( ((t * intervall), read * intervall))
            io[ "write"].append( ((t * intervall), write * intervall))

            tr = ( samples[t + 1][name]["time-read"] -
                samples[t][name]["time-read"])
            tw = ( samples[t + 1][name]["time-write"] -
                samples[t][name]["time-write"])

            #normalize
            time[ "read"].append( ((t * intervall), tr * intervall))
            time[ "write"].append( ((t * intervall), tw * intervall))

        #determine if device has io throughput
        if sigma == 0:
            continue

        #collect data for all devices
        io_read[ name] = io["read"]
        io_write[ name] = io["write"]
        time_read[ name] = time["read"]
        time_write[ name] = time["write"]

        #plotting MiB/s
        title =  "/proc/diskstats Reading/Writing %s" % name
        filename = "%s/diskstats-%s.svg" % ( test_dir, name)
        g = graphing.init( title, filename)
        g( "set key outside")
        g( "set xlabel 'Runtime ( sec)'")
        g( "set ylabel 'MiB/s'")
        graphing.series( io, g)
        g.close()

        #plotting time spent on io
        title =  "/proc/diskstats Time Spent on IO %s" % name
        filename = "%s/diskstats-%s-time.svg" % ( test_dir, name)
        g = graphing.init( title, filename)
        g( "set key outside")
        g( "set xlabel 'Runtime ( sec)'")
        g( "set ylabel 'ms/s'")
        graphing.series( time, g)
        g.close()

    #graphs for all devices

    #plotting io read for all devices
    title =  "/proc/diskstats IO Reading"
    filename = "%s/diskstats-read.svg" % ( test_dir)
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set xlabel 'Runtime ( sec)'")
    g( "set ylabel 'MiB/s'")
    graphing.series( io_read, g)
    g.close()

    #plotting io write for all devices
    title =  "/proc/diskstats IO Writing"
    filename = "%s/diskstats-write.svg" % ( test_dir)
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set xlabel 'Runtime ( sec)'")
    g( "set ylabel 'MiB/s'")
    graphing.series( io_write, g)
    g.close()

    #plotting time read for all devices
    title =  "/proc/diskstats Time Spent Reading"
    filename = "%s/diskstats-time-read.svg" % ( test_dir)
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set xlabel 'Runtime ( sec)'")
    g( "set ylabel 'ms/s'")
    graphing.series( time_read, g)
    g.close()

    #plotting time write for all devices
    title =  "/proc/diskstats Time Spent Writing"
    filename = "%s/diskstats-time-write.svg" % ( test_dir)
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set xlabel 'Runtime ( sec)'")
    g( "set ylabel 'ms/s'")
    graphing.series( time_write, g)
    g.close()
