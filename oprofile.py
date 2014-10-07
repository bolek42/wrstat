#oprofile
import os
import csv
import shutil
import operator
import subprocess
from sets import Set

import graphing
from utils import *

#TODO callgraph. extra filtred callers and callee graphs?

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
    if os.getuid() == 0:
        tool_path = get_tool_path()
        subprocess.call( [ "bash", "%s/oprofile-init.sh" % tool_path, test_dir])
    else:
        print "ERROR: Oprofile requires root previleges"

def sample( test_dir, t):
    pass

def postsampling( test_dir):
    if os.getuid() == 0:
        tool_path = get_tool_path()
        subprocess.call( [ "bash", "%s/oprofile-deinit.sh" % tool_path, test_dir])


#########################################
#       Parsing samples                 #
#########################################

def parse( test_dir):
    if not os.path.isfile( "%s/samples/oprofile" % test_dir):
        return None

    #read and sanitize data
    file = open( "%s/samples/oprofile" % test_dir, "r")
    raw = csv.reader( file, delimiter=' ')
    rows = map( lambda row: filter(lambda s: s != '', row), raw)

    n_cpu = 0
    data = []
    for row in rows:
        #skip header rows
        if len( row) < 4 or not row[0].isdigit():
            continue

        #determine number of cpus
        if n_cpu == 0:
            n_cpu = (len ( row) / 2) - 1

        #process fields for each row
        line = dict()
        samples_aggregate = 0.0
        runtime_aggregate = 0.0
        for cpu in range( n_cpu):
            sample = int( row[cpu * 2])
            runtime = float( row[(cpu * 2) + 1])
            line[ "samples_cpu%d" % cpu] = sample
            line[ "runtime_cpu%d" % cpu] = runtime
            samples_aggregate += sample
            runtime_aggregate += runtime

        line[ "samples_aggregate"] = samples_aggregate
        line[ "runtime_aggregate"] = runtime_aggregate
        line[ "app_name"] = row[ -2]
        line[ "symbol_name"] = row[ -1]

        data.append( line)

    oprof = {}
    oprof[ "rows"] = data
    oprof[ "n_cpu"] = n_cpu

    return oprof #returns n_cpu and data


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, data, intervall):
    if data is None or len( data["rows"]) == 0:
        return

    #plot unfiltred data
    discarded = {}
    for key in data["rows"][0]:
        if key == "app_name" or key == "symbol_name":
            continue
        discarded[ key] = 0.0

    file_prefix = "%s/oprofile" % test_dir
    filter_title = ""
    plot_info( file_prefix, filter_title, data, intervall, discarded)

    #loading config
    config = load_config( "%s/wrstat.config" % test_dir)

    #filtering data by appname
    filter_all = Set()
    filters = config[ "oprofile_app_filter"]
    if isinstance( filters, basestring):
        filters = [ filters]
    for f in filters:
        print "%s: processing app filter filter %s" % ( __file__, f)

        #create filter set
        s = Set()
        s.add( f.strip())
        filter_all |= s

        file_prefix = "%s/oprofile-app-filter-%s" % ( test_dir, f.replace( "/", "_"))
        filter_title = "Filtred (App): %s" % f
        plot_filter( data, s, intervall, file_prefix, filter_title, filter_key="app_name")

    file_prefix = "%s/oprofile-app-filter-all" % ( test_dir)
    filter_title = "Filtred by all filers (App)"
    plot_filter( data, filter_all, intervall, file_prefix, filter_title, filter_key="app_name")

    #filtering data by symbolname
    filter_all = Set()
    filters = config[ "oprofile_sym_filter"]
    if isinstance( filters, basestring):
        filters = [ filters]
    for f in filters:
        if not os.path.isfile( "%s/%s" % (config["tool_path"], f)):
            print "%s: missing sym filter %s" % ( __file__, f)
            continue

        print "%s: processing sym filter %s" % ( __file__, f)

        #create filter set
        s = Set()
        for line in open( "%s/%s" % (config["tool_path"], f), "r"):
            s.add( line.strip())
        filter_all |= s

        file_prefix = "%s/oprofile-sym-filter-%s" % ( test_dir, f.replace( "/", "_"))
        filter_title = "Filtred (Sym): %s" % f
        plot_filter( data, s, intervall, file_prefix, filter_title)

    file_prefix = "%s/oprofile-sym-filter-all" % ( test_dir)
    filter_title = "Filtred by all filers (Sym)"
    plot_filter( data, filter_all, intervall, file_prefix, filter_title)


def plot_filter( data, s, intervall, file_prefix, filter_title, filter_key="symbol_name"):
    #determine discarded samples
    discarded = {}
    for key in data["rows"][0]:
        if key == "app_name" or key == "symbol_name":
            continue
        discarded[ key] = 0.0

    rows = []
    has_data = False
    for row in data["rows"]:
        if row[ filter_key] in s:
            rows.append( row)
            has_data = True
        else:
            for key in data["rows"][0]:
                if key == "app_name" or key == "symbol_name":
                    continue
                discarded[ key] += row[ key]

    if has_data:
        filtred = { "n_cpu" : data[ "n_cpu"], "rows" : rows}
        plot_info( file_prefix, filter_title, filtred, intervall, discarded)



def plot_info( prefix, filter_title, data, intervall, discarded):
    if data is None or len( data["rows"]) == 0:
        return

    n_cpu = data[ "n_cpu"]
    rows = data[ "rows"]
    #separate plot
    for cpu in range( n_cpu):
        file_prefix = "%s-cpu%d" % ( prefix, cpu)
        title_prefix = "Total Runtime CPU %d %s" % ( cpu, filter_title)
        plot_histogram( file_prefix, rows, "samples_cpu%d" % cpu, title_prefix, discarded)

    #aggregated plot
    file_prefix = "%s-aggregate" % prefix
    title_prefix = "Total Runtime Aggregate %s" % filter_title
    plot_histogram( file_prefix, rows, "samples_aggregate", title_prefix, discarded)

def plot_histogram( file_prefix, rows, key, title_prefix, discarded):
    rows = sorted( rows, key=lambda row: row[key])

    #prepare data for symbol names
    data = {}
    sigma = 0.0
    for row in rows:
        sigma += float( row[key])
        data[ row["symbol_name"]] = [float( row[key])]

    if sigma == 0:
        return

    #actual plotting
    title = "Oprofile %s (Symbol Names)" % title_prefix
    filename = "%s-sym.svg" % file_prefix
    g = graphing.init( title, filename)
    graphing.histogram_percentage( data, discarded[key], g)
    g.close()

    #prepare data for app names
    apps = {}
    for row in rows:
        if row["app_name"] not in apps:
            apps[ row["app_name"]] = 0.0

        apps[row["app_name"]] += row[key]

    data = {}
    for app, usage in sorted( apps.iteritems(), key=operator.itemgetter(1)):
        data[ app] = [float( usage)]

    #actual plotting
    title = "Oprofile %s (App Names)" % title_prefix
    filename = "%s-app.svg" % file_prefix
    g = graphing.init( title, filename)
    graphing.histogram_percentage( data, discarded[key], g)
    g.close()
