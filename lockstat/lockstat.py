#/proc/lockstat

import csv

import graphing

def parse_lock_class( row, keys):
	if len( row) <= len( keys):
		print "invalid usage row"
		return None

	lockname = row[ 0 : len( row) - len( keys)]
	lockname = " ".join( lockname)
	lockname = lockname[0:-1]

	data = row[ len( row) - len( keys) ::]

	usage = {}
	usage[ "name"] = lockname
	usage[ "read-locks"] = []
	usage[ "write-locks"] = []

	for key, value in zip(keys, data):
		usage[ key] = float( value)
		
	return usage

def parse_lock( row, offset):
	lock = {}
	lock[ "con-bounces"] = int( row[offset])
	lock[ "addr"] = row[offset + 1]
	lock[ "symbol"] = row[offset + 2]

	return lock

def parse( filename):
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
	for row in rows:
		if len( row) == 0:
			pass
		elif len(row) == 1 and row[0][0] == '-':
			if state == "lock_class":
				state = "read_lock" #FIXME inverse?
			elif state == "read_lock":
				state = "write_lock"

		elif len(row) == 1 and row[0][0] == '.':
			state = "lock_class"
		elif state == "lock_class":
			lock_class = parse_lock_class( row, keys)
			if not( lock_class is None):
				lock_classes.update( { lock_class["name"] : lock_class})
		elif state == "read_lock":
			name_offset = lock_class["name"].count( ' ')  + 1
			lock = parse_lock( row, name_offset)
			if not( lock is None):
				lock_class["read-locks"].append( lock)
		elif state == "write_lock":
			name_offset = lock_class["name"].count( ' ')  + 1
			lock = parse_lock( row, name_offset)
			if not( lock is None):
				lock_class["write-locks"].append( lock)

	file.close()
	return lock_classes

def plot_topn_detailed( samples, sample_rate, sort_key, n, path):
	#determine top n
	top_names = []
	for key, value in samples[-1].iteritems():
		top_names.append( value)

	top_names = sorted( top_names, key=lambda x: x[sort_key], reverse = True)
	
	#actual plot
	locks = {}
	for i in range( n):
		class_name = top_names[i]["name"]

		#calculating curves
		waittime = []
		contentions = []
		con_bounce = []
		acquisitions = []
		for t in range( len( samples) - 1):
			if class_name in samples[t]:
				wt = ( samples[t+1][ class_name]["waittime-total"] - 
					samples[t][ class_name]["waittime-total"]   )

				aq = ( samples[t+1][ class_name]["acquisitions"] - 
					samples[t][ class_name]["acquisitions"]   )
				ct = ( samples[t+1][ class_name]["contentions"] - 
					samples[t][ class_name]["contentions"]   )
				cb = ( samples[t+1][ class_name]["con-bounces"] - 
					samples[t][ class_name]["con-bounces"]   )

			else:
				wt = aq = ct = cb = 0.0

			waittime.append( (t / float( sample_rate), wt * sample_rate))
			acquisitions.append( (t / float( sample_rate), aq * sample_rate))
			contentions.append( (t / float( sample_rate), ct * sample_rate))
			con_bounce.append( (t / float( sample_rate), cb * sample_rate))

		#FIXME term read_locks
		#build histogram data structure
		locks = {}
		for lock in samples[-1][ class_name]["read-locks"]:
			symbol_name = lock["symbol"]
			con_bounces = lock["con-bounces"]
			locks[ "(r) %s" % symbol_name] = [ con_bounces]

		for lock in samples[-1][ class_name]["write-locks"]:
			symbol_name = lock["symbol"]
			con_bounces = lock["con-bounces"]
			locks[ "(w) %s" % symbol_name] = [ con_bounces]
			
		#FIXME graphing
		#plot
		g = graphing.init( class_name, "%s/top-%d.svg" % ( path, i))

		g( "set multiplot")

		g( "set origin 0,0.45")
		g( "set size 0.5,0.5")

		cmds = [ "set ylabel 'wait us/s'"]
		data = {}
		data[ "Waittime"] = waittime
		graphing.series( data, "", "Waittime", cmds, g)

		g("unset object 1")

		g( "set ylabel '#/s'")
		g( "set logscale y")
		g( "set key bottom right")
		g( "set key outside")
		g( "set key bmargin")
		g( "set key horizontal")
		g( "set origin 0.5,0.45")
		g( "set size 0.5,0.5")

		g( "set title 'Acquisitions - Contentions'")

		cmds = [ "set ylabel '#/s'"]
		data = {}
		data[ "acqu."] =  acquisitions
		data[ "cont."] =  contentions
		graphing.series( data, "", "Acquisitions - Contentions", cmds, g)

		g( "unset logscale y")
		g( "set key default")

		#histogram
		g( "unset xtics")
		g( "set ylabel 'Bounces Total'")
		g( "set origin 0,0")
		g( "set size 1,0.5")

		g( "set title 'Bounces - Functions'")

		graphing.histogram_percentage( locks, "", "Read/Write", 0, [], g)

		g.close()

def plot( test_dir, samples, sample_rate):
	data = {}
	for (class_name, lock_class) in samples[-1].iteritems():
		data[ class_name] = [ lock_class[ "waittime-total"]]
	cmds = [ "unset xtics"]
	graphing.histogram_percentage( data, "%s/lockstat_waititme.svg" % test_dir, "Waittime Total", 0, cmds)

	data = {}
	for (class_name, lock_class) in samples[-1].iteritems():
		data[ class_name] = [ lock_class[ "holdtime-total"]]
	cmds = [ "unset xtics"]
	graphing.histogram_percentage( data, "%s/lockstat_holdtime.svg" % test_dir, "Holdtime Total", 0, cmds)

	#determine top n
	top_names = []
	for key, value in samples[-1].iteritems():
		top_names.append( value)

	top_names = sorted( top_names, key=lambda x: x["waittime-total"], reverse = True)
	
	#actual plot
	data = {}
	for lock_class in top_names[0:8]:
		series = []
		for i in range( len( samples) - 1):
			if lock_class["name"] in samples[i]:
				t = ( samples[i+1][ lock_class["name"]]["waittime-total"] - 
					samples[i][ lock_class["name"]]["waittime-total"]   )
			else:
				t = 0.0

			series.append( (i / float( sample_rate), t))

		data[ lock_class["name"]] = series

	cmds = [	"set key outside",
			"set key bottom right",
			"set key horizontal",
			"set key bmargin",
			"set xlabel 'runtime ( sec)'",
			"set ylabel 'usec/s'"]

	graphing.series( data, "%s/lockstat_waittime_top.svg" % test_dir, 'Waittime Top', cmds)

	#FIXME
	plot_topn_detailed( samples, 2, "waittime-total", 8, test_dir)
