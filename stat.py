#/prpc/stat

import os
import csv
import shutil

import graphing
from utils import *

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
    pass

def sample( test_dir, t):
    if os.path.isfile( "/proc/stat"):
        copy_queued( "/proc/stat", "%s/samples/stat_%d" % ( test_dir, t))

def postsampling( test_dir):
    pass


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
    t = 0
    samples = []

    while os.path.isfile( "%s/samples/stat_%d" % ( test_dir, t)):
        sample = parse_sample( "%s/samples/stat_%d" % ( test_dir, t))
        samples.append( sample)

        t+= 1

    return samples

def parse_sample( filename):
    file = open( filename, "r")

    raw = list( csv.reader( file, delimiter=' '))
    rows = map( lambda row: filter(lambda s: s != '', row), raw)

    stat = {}

    n_cpu = -1
    for row in rows:
        if row[0][0:3] == "cpu":
            name, cpu = parse_cpu_row( row)
            stat[ name] = cpu
            n_cpu += 1
        elif len( row) == 2:
            stat[ row[ 0]] = int( row[1])
        #TODO add missing

    stat["n_cpu"] = n_cpu
    return stat


def parse_cpu_row( row):
    cpu = {}
    name = row[0]
    cpu[ "user"] = int( row[1])
    cpu[ "nice"] = int( row[2])
    cpu[ "system"] = int( row[3])
    cpu[ "idle"] = int( row[4])
    if len( row) > 5:
        cpu[ "iowait"] = int( row[5])
    if len( row) > 6:
        cpu[ "irq"] = int( row[6])
    if len( row) > 7:
        cpu[ "softirq"] = int( row[7])
    if len( row) > 8:
        cpu[ "steal"] = int( row[8])
    if len( row) > 9:
        cpu[ "guest"] = int( row[9])
    if len( row) > 10:
        cpu[ "guest_nice"] = int( row[10])

    return name, cpu


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, stat, intervall):
    if len( stat) == 0:
        print "stat.py nothing captured"
        return
    if len( stat) == 1:
        print "stat.py: only one sample captured, skipping"
        return

    #aggregate
    title = "/proc/stat Aggreagted"
    filename = "%s/stat-aggreagted.svg" % test_dir
    plot_stat_series( stat, "cpu", filename, title, intervall)

    #prepare data
    data = {}
    for key, value in stat[0]["cpu"].iteritems():
        data[ key] = []

    #for all cpu...
    for cpu in range( stat[0]["n_cpu"]):
        for key, value in data.iteritems():
            value.append( stat[-1]["cpu%d" % cpu][key] -
                            stat[0]["cpu%d" % cpu][key])


        #per cpu sampled
        filename = "%s/stat-cpu%d.svg" % ( test_dir, cpu)
        title = "/proc/stat CPU %d" % cpu
        plot_stat_series( stat, "cpu%d" % cpu, filename, title, intervall)

    #determine width
    # 400 pixel offset
    # min 20 pixel per bar
    size = ( 400 + 20 * stat[0]["n_cpu"], 480)

    #aggregated
    title = "/proc/stat Total"
    filename = "%s/stat-total.svg" % test_dir
    g = graphing.init( title, filename, size)
    g( "set xlabel 'CPU'")
    graphing.histogram_percentage( data, 0, g, 15)
    g.close()

def plot_stat_series( stat, cpu, filename, title, intervall):
    #prepare graphs
    raw = {}
    for key, value in stat[0][cpu].iteritems():
        raw[ key] = []

    for t in range( len( stat) - 1):
        #normalize daa
        sigma = 0.0
        for key, value in raw.iteritems():
            sigma += stat[t + 1][cpu][key] - stat[t][cpu][key]

        for key, value in raw.iteritems():
            p = (stat[t + 1][cpu][key] - stat[t][cpu][key]) / sigma * 100.0
            value.append( ( t * intervall, p))

    #reindexing for total
    sigma = 0.0
    for key, value in stat[0][cpu].iteritems():
        sigma += stat[-1][cpu][key] - stat[0][cpu][key]

    data = []
    for key, value in stat[0][cpu].iteritems():
        p = (stat[-1][cpu][key] - stat[0][cpu][key]) / sigma * 100.0 #total
        data.append( ("%s (%.2f%%)" % ( key, p), raw[key]))

    #actual plotting
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set key bottom right")
    g( "set key horizontal")
    g( "set key bmargin")
    g( "set xlabel 'runtime ( sec)'")
    g( "set yrange [0:103]")
    g( "set ylabel 'Runtime %'")
    graphing.series( data, g, True)
    g.close()

