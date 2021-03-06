#/proc/lock_stat

import os
import csv
import subprocess
from sets import Set

import graphing
from utils import *

#########################################
#       Sampling methods                #
#########################################

def presampling( test_dir):
    if os.getuid() == 0:
        tool_path = get_tool_path()
        subprocess.call( [ "%s/lock_stat-reset.sh" % tool_path])
    else:
        print "ERROR: lock_stat requires root previleges"

def sample( test_dir, t):
    if os.path.isfile( "/proc/lock_stat") and os.getuid() == 0:
        tool_path = get_tool_path()
        copy_queued( "/proc/lock_stat", "%s/samples/lock_stat_%d" % ( test_dir, t))

def postsampling( test_dir):
    pass


#########################################
#       Parsing samples                 #
#       Note: tim units will be         #
#             converted to ms           #
#########################################

def parse( test_dir):
    t = 0
    samples = []

    while os.path.isfile( "%s/samples/lock_stat_%d" % ( test_dir, t)):
        sample = parse_sample( "%s/samples/lock_stat_%d" % ( test_dir, t))
        samples.append( sample)

        t+= 1

    return samples

def parse_sample( filename):
    file = open( filename, "r")

    raw = list( csv.reader( file, delimiter=' '))
    #remove whitespaces and empty
    raw = map( lambda row: filter(lambda s: s != '', row), raw)
    #lines discard version and header
    rows = raw[ 4::]

    #read keys from header line
    keys = []
    for k in raw[2][2:]:
        keys.append( k)

    lock_classes = {}
    #to track the type of the current row we use a simple DFA
    state = "lock_class"
    current_lock_classes = []
    for row in rows:
        if len( row) == 0:
            pass
        elif len(row) == 1 and row[0][0] == '-':
            if state == "lock_class":
                state = "contention_point"
            elif state == "contention_point":
                state = "contention_with_point"

        elif len(row) == 1 and row[0][0] == '.':
            state = "lock_class"
            current_lock_classes = []

        elif state == "lock_class":
            lock_class = parse_lock_class( row, keys)
            if not( lock_class is None):
                lock_classes.update( { lock_class["name"] : lock_class})
                current_lock_classes.append( lock_class)

        elif state == "contention_point":
            name_offset = lock_class["name"].count( ' ')  + 1
            cp = parse_contention_point( row, name_offset)
            if not( cp is None):
                for lc in current_lock_classes:
                    lc["contention-points"].append( cp)

        elif state == "contention_with_point":
            name_offset = lock_class["name"].count( ' ')  + 1
            cp = parse_contention_point( row, name_offset)
            if not( cp is None):
                for lc in current_lock_classes:
                    lc["contention-with-points"].append( cp)

    file.close()
    return lock_classes

def parse_lock_class( row, keys):
    if len( row) <= len( keys):
        print "invalid lock class row"
        return None

    lockname = row[ 0 : len( row) - len( keys)]
    lockname = " ".join( lockname)
    lockname = lockname[0:-1]

    data = row[ len( row) - len( keys) ::]

    lock_class = {}
    lock_class[ "name"] = lockname
    lock_class[ "contention-points"] = []
    lock_class[ "contention-with-points"] = []

    for key, value in zip(keys, data):
        #read keys from file
        #and convert time to ms
        if "time" in key:
            lock_class[ key] = float( value) / 1000.0
        else:
            lock_class[ key] = float( value)

    return lock_class

def parse_contention_point( row, name_offset):
    cp = {}
    cp[ "con-bounces"] = int( row[name_offset])
    cp[ "addr"] = row[name_offset + 1]
    symbol = row[name_offset + 2]
    try:
        offset = symbol[ symbol.index( '+') + 1:]
        symbol = symbol[ :symbol.index( '+')]
    except:
        offset = ""
    cp[ "symbol"] = symbol
    cp[ "offset"] = offset

    return cp


#########################################
#       Plotting data                   #
#########################################

def plot( test_dir, samples, intervall):
    if len( samples) < 2:
        return

    #unfiltred plots
    plot_samples( "%s/lock_stat" % test_dir, "",samples, intervall)

    #loading filter names
    tool_path = get_tool_path()
    config = load_config( "%s/wrstat.config" % test_dir)
    filters = config[ "lock_stat_filter"]
    if isinstance( filters, basestring):
        filters = [ filters]

    #filtering data
    filter_all = Set()
    for f in filters:
        if not os.path.isfile( "%s/%s" % (tool_path, f)):
            print "%s: missing filter %s" % ( __file__, f)
            continue

        print "%s: processing filter %s" % ( __file__, f)

        #create filter set
        s = Set()
        for line in open( "%s/%s" % (tool_path, f), "r"):
            s.add( line.strip())
        filter_all |= s

        file_prefix = "%s/lock_stat-filter-%s" % ( test_dir, f.replace( "/", "_"))
        filter_title = "Filtred: %s" % f
        plot_filter( samples, s, intervall, file_prefix, filter_title)

    print "%s: processing all filters" % ( __file__)
    file_prefix = "%s/lock_stat-filter-all" % ( test_dir)
    filter_title = "Filtred by all filers"
    plot_filter( samples, filter_all, intervall, file_prefix, filter_title)


#will process the actual filter s and call the plotting method
def plot_filter( samples, s, intervall, file_prefix, filter_title):
    #determine lock_classes that passes the filter
    class_names_filtred = Set() #set of lock names that passed the filter
    for sample in samples:
        for (class_name, lock_class) in sample.iteritems():
            discard = True
            # check if lock_class was used by function
            for lc in lock_class["contention-points"]:
                if lc["symbol"] in s:
                    discard = False
            for lc in lock_class["contention-with-points"]:
                if lc["symbol"] in s:
                    discard = False

            if not discard:
                class_names_filtred.add( class_name)

    #skip empty results
    if len( class_names_filtred) == 0:
        return

    #create filtred samles
    samples_filtred = []
    for sample in samples:
        sample_filtred = {}
        for (class_name, lock_class) in sample.iteritems():
            if class_name in class_names_filtred:
                sample_filtred[class_name] = lock_class

        samples_filtred.append( sample_filtred)

    #actually plotting data
    plot_samples( file_prefix, filter_title, samples_filtred, intervall)


def plot_samples( file_prefix, title_prefix, samples, intervall):
    #preparing data
    data = {}
    for (class_name, lock_class) in samples[-1].iteritems():
        data[ class_name] = [ lock_class[ "waittime-total"]]

    #actual plotting
    title =  "%s /proc/lock_stat Waittime Total" % title_prefix
    filename = "%s-waittime.svg" % file_prefix
    g = graphing.init( title, filename)
    graphing.histogram_percentage( data, 0, g)
    g.close()

    #preparing data
    data = {}
    for (class_name, lock_class) in samples[-1].iteritems():
        data[ class_name] = [ lock_class[ "holdtime-total"]]

    #actual plotting
    title =  "%s /proc/lock_stat Holdtime Total" % title_prefix
    filename = "%s-holdtime.svg" % file_prefix
    g = graphing.init( title, filename)
    graphing.histogram_percentage( data, 0, g)
    g.close()

    #determine top locks in respect to total wait time
    top = []
    for lock_name, lock_class in samples[-1].iteritems():
        top.append( lock_class)
    top = sorted( top, key=lambda x: x["waittime-total"], reverse = True)

    #time series and detailed plot for top locks
    wait = {}
    hold = {}
    rank = 1
    for lock_class in top[0:8]:
        lock_name = lock_class["name"]

        #detailed plot
        plot_detailed( file_prefix, title_prefix, samples, intervall, lock_name, rank)
        rank += 1

        #preparing data
        waittime = []
        holdtime = []
        w_sum = 0.0
        h_sum = 0.0
        for t in range( len( samples) - 1):
            if lock_name in samples[t] and lock_name in samples[t+1]:
                wt = ( samples[t+1][ lock_name]["waittime-total"] -
                    samples[t][ lock_name]["waittime-total"]   )
                ht = ( samples[t+1][ lock_name]["holdtime-total"] -
                    samples[t][ lock_name]["holdtime-total"]   )
            else:
                wt = ht = 0.0

            w_sum += wt / intervall
            h_sum += ht / intervall
            waittime.append( (t * intervall, wt / intervall))
            holdtime.append( (t * intervall, ht / intervall))

        w_mean = w_sum / (len( samples)-1)
        h_mean = h_sum / (len( samples)-1)

        wait[ "%s (%.2f ms/s)" % ( lock_class["name"], w_mean)] = waittime
        hold[ "%s (%.2f ms/s)" % ( lock_class["name"], h_mean)] = holdtime

    #actual plotting waittime
    title = "%s /proc/lock_stat Waittime Top" % title_prefix
    filename = "%s-waittime-top.svg" % file_prefix
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set key bottom right")
    g( "set key horizontal")
    g( "set key bmargin")
    g( "set xlabel 'runtime ( sec)'")
    g( "set ylabel 'ms/s'")
    graphing.series( wait, g)
    g.close()

    #actual plotting holdtime
    title = "%s /proc/lock_stat Holdtime Top ( Ordered by Waittime)" % title_prefix
    filename = "%s-holdtime-top.svg" % file_prefix
    g = graphing.init( title, filename)
    g( "set key outside")
    g( "set key bottom right")
    g( "set key horizontal")
    g( "set key bmargin")
    g( "set xlabel 'runtime ( sec)'")
    g( "set ylabel 'ms/s'")
    graphing.series( hold, g)
    g.close()

def plot_detailed( file_prefix, title_prefix, samples, intervall, lock_name, rank):
    #calculating curves
    waittime = []
    holdtime = []
    contentions = []
    con_bounce = []
    acquisitions = []
    for t in range( len( samples) - 1):
        if lock_name in samples[t] and lock_name in samples[t+1]:
            #wait and holdtime in ms
            wt = ( samples[t+1][ lock_name]["waittime-total"] -
                samples[t][ lock_name]["waittime-total"]   )
            ht = ( samples[t+1][ lock_name]["holdtime-total"] -
                samples[t][ lock_name]["holdtime-total"]   )

            aq = ( samples[t+1][ lock_name]["acquisitions"] -
                samples[t][ lock_name]["acquisitions"]   )
            ct = ( samples[t+1][ lock_name]["contentions"] -
                samples[t][ lock_name]["contentions"]   )
            cb = ( samples[t+1][ lock_name]["con-bounces"] -
                samples[t][ lock_name]["con-bounces"]   )

        else:
            wt = ht = aq = ct = cb = 0.0

        waittime.append( (t * intervall, wt / intervall))
        holdtime.append( (t * intervall, ht / intervall))
        acquisitions.append( (t * intervall, aq / intervall))
        contentions.append( (t * intervall, ct / intervall))
        con_bounce.append( (t * intervall, cb / intervall))

    #build histogram data structure
    contention_points = {}
    for contention_point in samples[-1][ lock_name]["contention-points"]:
        symbol_name = contention_point["symbol"]
        offset = contention_point["offset"]
        con_bounces = contention_point["con-bounces"]
        contention_points[ "%s+%s" % (symbol_name, offset)] = [ con_bounces]

    contention_with_points = {}
    for contention_with_point in samples[-1][ lock_name]["contention-with-points"]:
        symbol_name = contention_with_point["symbol"]
        offset = contention_with_point["offset"]
        con_bounces = contention_with_point["con-bounces"]
        contention_with_points[ "%s+%s" % (symbol_name, offset)] = [ con_bounces]

    #actual plotting
    title = "%s /proc/lock_stat Top %d: %s" % ( title_prefix, rank, lock_name)
    filename =  "%s-top-%d.svg" % ( file_prefix, rank)
    g = graphing.init( title, filename)
    g( "set multiplot")

    #Waittime subplot
    g( "set origin 0,0.55")
    g( "set size 0.5,0.4")
    g( "set title 'Wait-/Holdtime'")
    g( "set ylabel 'ms/s'")
    g( "set key bottom right")
    g( "set key outside")
    g( "set key bmargin")
    g( "set key horizontal")
    graphing.series( {"Waittime" : waittime, "Holdtime" : holdtime}, g)

    g("unset object 1")

    #Acquisitions - Contentions subplot
    g( "set origin 0.5,0.55")
    g( "set size 0.5,0.4")
    g( "set title 'Acquisitions - Contentions'")
    g( "set ylabel '#/s'")
    g( "set logscale y")
    graphing.series( {"acqu." : acquisitions, "cont." :  contentions}, g)
    g( "unset logscale y")
    g( "set key default")

    #Contentions subplot
    g( "unset title")
    g( "set ylabel 'Contentions'")
    g( "set origin 0,0.27")
    g( "set size 1,0.30")
    graphing.histogram_percentage( contention_points, 0, g, 50)

    #Contentions subplot
    g( "set ylabel 'Contentions With'")
    g( "set origin 0,0")
    g( "set size 1,0.30")
    graphing.histogram_percentage( contention_with_points, 0, g, 50)

    g.close()

