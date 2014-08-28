import Gnuplot, Gnuplot.funcutils

colors = [ 	
		'#FF0000', '#00FF00', '#0000FF', 
		'#008888', '#880088', '#888800', 
		'#0088FF', '#FF8800', '#88FF00',
		'#004444', '#440044', '#444400',
		'#880000', '#008800', '#000088', 
		'#440000', '#004400', '#000044', 
		'#00FF88', '#88FF00', '#FF8800',
		'#000000']

def init( title, filename, size=(640, 480)):
	g = Gnuplot.Gnuplot( debug=0)
	g( "set terminal svg size %d %d" % size)
	g( "set output '%s'" % filename)
	g( "set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb'white' behind")

	#set title on center of the screen
	g( "set title ' '")
	g( "set label 1 '%s' at screen 0.5,0.95 center" % title)
	return g

"""
	Data format:
		{ "curve 1" : [ (0,0), (1,1), (2,2), (3,3)],
		  "curve 2" : [ (0,0), (1,1), (2,4), (3,9)]}
"""
def series( data, g):
	if g is None:
		print "ERROR no gnuplot object given"
		return

	plots = []
	i = 0
	for name, series in data.iteritems():
		plots.append( Gnuplot.PlotItems.Data( series,
			with_="lines linecolor rgb '%s'" % colors[ i % len( colors)], title=str(name)))
		i += 1

	g.plot( *plots)


"""
	For a 3 bar histogram

	Data format:
		{ "class 1" [ 1, 6, 2]
		{ "class 2" [ 3, 5, 1]}
"""
def histogram( data, g, title_len=40):
	#prepare data
	histogram = []
	n_samples = 0
	for key, value in sorted( data.iteritems(), key=lambda (key, value): value[0]):
		#truncate title
		key = key[ 0: title_len]
		key += " " * ( title_len - len( key))

		pl = Gnuplot.PlotItems.Data( value, title=key)
		histogram.append( pl)

		if len( value) > n_samples:
			n_samples = len( value)

	#histogram
	g( "set style data histograms")
	g( "set style histogram rowstacked")
	g( "set style fill solid border -1")
	g( "set key invert reverse Left outside")

	#setting xtics
	if n_samples == 1:
		g( "unset xtics")
	else:
		g( "set xtics 1")
		g( "set xrange [-0.5:%.1f]" % (n_samples - 0.5))

	g.plot(	*histogram)


def histogram_percentage( data, discarded, g, title_len=40):
	#determine total sum of all bars including discarded samples
	sigma = None
	n_samples = 0

	for key, values in data.iteritems():
		if sigma is None:
			n_samples = len( values)
			sigma = [ discarded] * n_samples #TODO array support

		if len( values) != n_samples:
			print "Graphing Error: invalid number of samples in plot_histogram_percentage"
			return

		for i in range( n_samples):
			sigma[ i] += values[i]

	#normalize values to percentage
	others = [0.0] * n_samples
	percentage = [ 0.0] * n_samples
	normalized = {}

	#in respect to discarded samples
	yrange  = 0
	for i in range( n_samples):
		p = 100.0 - discarded * 100.0 / sigma[i]
		others[i] = p
		yrange = max( yrange, p)

	for key, values in sorted( data.iteritems(), key=lambda (key, value): value, reverse=True)[0:16]:
		#over all samples
		for i in range( n_samples):
			percentage[i] = values[i] * 100.0 / sigma[i]
			others[i] -= percentage[i]

		#give gnuplot the category key
		if n_samples == 1:
			normalized[ "(%.2f%%) %s" % (percentage[0], str( key))] = list( percentage)
		else:
			normalized[ key] = list( percentage)

	#others category
	if n_samples == 1:
		if others[0] > 0.5:
			normalized[ "(%.2f%%) others" % others[0]] = others
	else:
		show_others = False
		for o in others:
			if o > 0.5:
				show_others = True

		if show_others:
			normalized[ "others"] = others

	#actual gnuplot stuff
	g( "set yrange [0:%f]" % yrange)
	g( "set ylabel 'Runtime Percentage'")

	histogram( normalized, g, title_len)

