import imp
import csv

def load_config( filename): 
	#read samplerate from config
	file = open( filename, "r")
	raw = list( csv.reader( file, delimiter=' '))
	rows = map( lambda row: filter(lambda s: s != '', row), raw)

	config = {}
	for row in rows:
		if len( row) == 2:
			config[ row[0]] = row[ 1:][0]
		elif len( row) > 2:
			config[ row[0]] = row[ 1:]

	return config

def load_modules( modnames):
	if isinstance( modnames, basestring):
		modnames = [ modnames]

	modules = {}
	for modname in modnames:
		try:
			modules[ modname] =  imp.load_source( modname, "%s.py" % modname)
		except:
			print "error loading %s" % modname
			raise 

	return modules
