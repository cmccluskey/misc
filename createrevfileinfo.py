#!/usr/bin/python
import argparse
import sys
import os
import pprint

parser = argparse.ArgumentParser(description='Using a current extension.dict (and possible defaultext.dict) build out a reverse extension dictionary')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out')
parser.add_argument('-i', dest='extdictf', required=True, help='Extension dict to be input; normal operating location is ./dicts/extension.dict')
parser.add_argument('-f', dest='defaultdictf', required=True, help='Use the following file to provide the default extension or create if absent based on current dicts; normal operating location is ./dicts/defaultext.dict')
parser.add_argument('-o', dest='revdictf', required=True, help='Output filename for the Reverse Extension dict; normal operating location is ./dicts/revextension.dict')

# True out arg parser
args = parser.parse_args()
if args.debug: print(args)

# Load the ext dict
execfile(os.path.abspath(args.extdictf)) 
if (len(extdict.keys()) < 2):
	print "Error: Cannot load dict %s. Not enough records loaded (%s)." % (extdictf,len(extdict.keys()))
	sys.exit(1)
else: 
	if args.debug: print "Info: %s keys loaded into extdict." % (len(extdict.keys()))

# Attempt to load the defaultext dict
try:
	defaultf = open(os.path.abspath(args.defaultdictf), 'r')
except IOError:
	if args.debug: print "Info: Cannot load defaultext dict from %s - will create later." % (os.path.abspath(args.defaultdictf))
	defaultloaded=False
else:
	exec(defaultf)
	if (len(defaultext.keys()) < 2):
		print "Error: Cannot load dict %s. Not enough records loaded (%s)." % (defaultdictf,len(defaultext.keys()))
		defaultloaded=False
	else:
		if args.debug: print "Info: %s keys loaded into defaultdict." % (len(defaultext.keys()))
		defaultloaded=True
	defaultf.close

# Construct the revextension dict
# Description -> Extension : Reference Count
revextension = {}
for extension in extdict:
	for description in extdict[extension]:
		if description not in revextension.keys():
			revextension[description]= {}
		else: None
		revextension[description][extension] = extdict[extension][description]

# If no defaultext present, create one and write to disk
if not defaultloaded:
	defaultext = {}
	for description in revextension:
		largest = None
		count = 0
		if (len(revextension[description]) > 0):
			for key in revextension[description]:
				if revextension[description][key] > count:
					largest = key 
					count = revextension[description][key]
					if args.debug: print "Debug: Marking key %s as the largest (%s) in %s." % (key, count, description)
				else: None
			defaultext[description] = {}
			defaultext[description]['DEFAULT'] = []
			defaultext[description]['DEFAULT'].append(largest)
		else:
			if args.debug: print "Info: There is only one extension, %s, for description, %s." % (key, description)
	# Write out defaultext
	try:
		outf = open(os.path.abspath(args.defaultdictf), 'w')
	except IOError:
		if args.debug: print "Error: Cannot write defaultext dict to %." % (os.path.abspath(args.defaultdictf))
	else:
		outf.write("defaultext = ")
        	pp = pprint.PrettyPrinter(indent=1,stream=outf)
        	pp.pprint(defaultext)
        	outf.close
else: None

# Merge the defaultext to revextension
for description in revextension:
	if description in defaultext.keys():
		revextension[description].update(defaultext[description])
	else: None

# Write out revextension
try:
	outf = open(os.path.abspath(args.revdictf), 'w')
except IOError:
	if args.debug: print "Error:  Cannot write revextension dict to %." % (os.path.abspath(args.revdictf))
else:
	outf.write("revextension = ")
	pp = pprint.PrettyPrinter(indent=1,stream=outf)
	pp.pprint(revextension)
	outf.close

