#!/usr/bin/python
import argparse
import sys
import pprint
from magicfixup import magicfixup

# Note: The Main Dictionary is "extensions" -> Sub Dictionary is the externsion of the file in the list -> Key is the shortened Magic Description in the data file -> Value is a Reference Counter

parser = argparse.ArgumentParser(description='Having a list from getfileinfo.py pull in the data and build out a reference dictionary of extensions')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out')
parser.add_argument('-i', dest='filename', required=True, help='Input filename for list')

# True out arg parser
args = parser.parse_args()
if args.debug: print(args)

# Define root dictionary
extensions = {}

# Open input file
try:
	inf = open(args.filename, 'r')
except IOError:
	print "Error: Skipping file %s due to access perimissions" % testfile
	sys.exit()
else:
	for line in inf:
		(extension, description, mimetype, filename) = line.split('\t')
		# Cleanup description to strip out per-file data
		description = magicfixup(description,args.debug)
		if args.debug: print "Debug: extension:%s, description:%s" % (extension,description)

		if extension not in extensions:
			extensions[extension] = {}
		else:
			None

		if description not in extensions[extension]:
#			extensions[extension].update({description: 1})
			extensions[extension][description] = 1
		else:
			extensions[extension][description] += 1


pp = pprint.PrettyPrinter(indent=4)
pp.pprint(extensions)

# Close input filehandle
inf.close
