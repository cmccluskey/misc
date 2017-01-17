#!/usr/bin/python
import argparse
import os
import magic
# brew install libmagic
# via pip install python-magic
# export PYTHONPATH=/usr/local/lib/python2.7/site-packages
import sys
import re
#import stat
from magicfixup import magicfixup
from datetime import datetime

# Variables
reportfile_ext  = '.tmp'

# Counters
countTotal      = 0 # Scanned plus all no-scan cases
countScanned    = 0 # Scanned cases total (see below)
countNoAccess   = 0 # Unscanned
countSkipped    = 0 # Unscanned
countExcluded   = 0 # Unscanned

# Counters of scanned items
countCorrect    = 0
countCase       = 0
countVariant    = 0
countIncorrect  = 0
countMissingExt = 0
countSymLink    = 0

# Timers
startTime       = datetime.now()
endTime         = 0

# Ok to process based on exlude list
def excludeRootCheckPassed(checkfile, myList):
	checkfile = os.path.dirname(checkfile)
        for x in myList:
                regex = '^' + re.escape(x)
                if re.search(regex,checkfile):
                        return False
                else:
                        None
        return True

def excludeDirCheckPassed(checkfile, myList):
	checkfile = os.path.dirname(checkfile)
	for x in myList:
        	regex = '^' + re.escape(x)
		if re.search(regex,checkfile):
			return False
		else: None
	return True

def writeLog(handles, line):
	for handle in handles:
		handle.write(line)
		handle.write('\n')
	return True

# Parser setup
parser = argparse.ArgumentParser(description='Validate files and thier extensions based on Magic description. Either report, rewrite, or move files that don\'t conform to the dictionary.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-e', dest='revextdict', default='./dicts/revextension.dict', help='Override the location of the extension dictionary.') 
parser.add_argument('-p', dest='path', required=True, help='Root path to start validation run.')
parser.add_argument('-C', dest='case', default='lower', nargs=1, choices=['upper','lower','stored'], help='Specify case (default lower).')
parser.add_argument('-r', dest='reportfile', default=False, help='Enable a report, and store the report at this location. If run without other operation, only the report of what would be done will be written.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Normally skipped, unavailable, and ok files are not written to the report, this enables those entries in the report.') 
parser.add_argument('-c', dest='caserun', action='store_true', default=False, help='Perform a modify case run.')
parser.add_argument('-m', dest='movedir', default=False, help='Perform a moving run by specififying a destination subdirectory relative to the current filename. You can provide a full path to move to a set location.')
parser.add_argument('-n', dest='namerun', action='store_true', default=False, help='Perform a rename-in-place run, modifying the suffix and case in place.')

# True out arg parser
args = parser.parse_args()

# Make sure one of the primary validation modes is set
if not (args.reportfile or args.caserun or args.movedir or args.namerun):
	parser.print_help()
	print "\n"
	print "Error: One of the runtime modes must be to run a report (-r), change the case (-c), move nonconforming files to a directory (-m), to rename in place (-n)."
	sys.exit(1)
else: None

# Make sure that there isn't more than one validation mode set
if ( (args.caserun and args.movedir and args.namerun) or (args.caserun and args.namerun) or (args.caserun and args.movedir) or (args.movedir and args.namerun) ):
	parser.print_help()
	print "\n"
	print "Error: The runtime mode must be only one of changing the case (-c), move nonconforming files to a directory (-m), to rename in place (-n)."
	sys.exit(1)
else: None

# Don't navigate these root paths
# TODO: Add as argument or config file
exclude_paths = ['/dev','/tmp','/Volumes']

# Don't navigate paths containing the following strings (useful if you have long lived directories from the rumtime mode move)
# TODO: Add as argument or config file
exclude_directories = ['_badsuffix']


# Validate and add movedir to the proper exclude bucket
if args.movedir:
	movedir_clean = args.movedir.rstrip('/')
	if not excludeRootCheckPassed(args.movedir, ['/']):
		movedir_clean = os.path.abspath(movedir_clean)
		exclude_paths.append(movedir_clean)
	else:
		movedir_clean = os.path.basename(movedir_clean)
		exclude_directories.append(movedir_clean)
else: None

# Open temporary report file
if args.reportfile:
	try:
		outf = open(os.path.abspath(args.reportfile + reportfile_ext), 'w')
	except IOError:
		print "Error: Cannot open temp reportfile %s." % ((args.reportfile + reportfile_ext))
		sys.exit(1)
else: None

# Setup active logging handles
active_log_handles = []

if args.reportfile:
	active_log_handles.append(outf)
else: None

if args.debug:
	active_log_handles.append(sys.stdout)
else: None

writeLog(active_log_handles, "Debug: %s" % args) 
writeLog(active_log_handles, "Debug: %s" % exclude_paths)
writeLog(active_log_handles, "Debug: %s" % exclude_directories)

# Attempt to load the revextension dict
try:
       inf = open(os.path.abspath(args.revextdict), 'r')
except IOError:
       writeLog(active_log_handles, "Error: Cannot load revextension dict from %s." % (os.path.abspath(args.revextdict)))
       sys.exit(1)
else:
       exec(inf)
       if (len(revextension.keys()) < 2):
               writeLog(active_log_handles, "Error: Cannot load dict %s. Not enough records loaded (%s)." % (revextdict,len(revextension.keys())))
               sys.exit(1)
       else:
               writeLog(active_log_handles, "Info: %s keys loaded into revextension dict." % (len(revextension.keys())))
       inf.close

# Walk the tree and write out line
for root, dirs, files in os.walk(args.path):
	for file in files:
	countTotal += 1
		testfile =  os.path.join(root, file)
		# Check for excluded paths from root
		if excludeRootCheckPassed(testfile,exclude_paths):
			# Check excluded directories
			if excludeCheckPassed(testfile,exclude_directories) 
			# Check for a symlink which messes with the socket check
			if os.path.islink(testfile):
				countSkipped +=1
				if (args.verbose): writeLog(active_log_handles, "%s skipped as a symlink." % (testfile))
                                elif (args.debug): print "%s skipped as a symlink." % (testfile))
                                else: None
			else:
				# Readable as the current user
				try:
					fp = open(testfile,'r')
				except IOError:
					countNoAccess +=1
					if (args.verbose): writeLog(active_log_handles, "%s skipped due to access permissions." % (testfile))
					elif (args.debug): print "%s skipped due to access permissions." % (testfile))
					else: None
				else:
					fp.close
				        # Checking to see if file is a socket
        				mode = os.stat(testfile).st_mode
        				if stat.S_ISSOCK(mode):
						countSkipped += 1
						if (args.verbose): writeLog(active_log_handles, "%s skipped as a named socket/pipe." % (testfile))
						elif (args.debug): print "%s skipped as a named socket/pipe." % (testfile))
						else: None
        				else:   
#countTotal      = 0 # Scanned plus all no-scan cases
#countScanned    = 0 # Scanned cases total (see below)
#countNoAccess   = 0 # Unscanned
#countSkipped    = 0 # Unscanned
#countExcluded   = 0 # Unscanned

# Counters of scanned items
#countCorrect    = 0
#countCase       = 0
#countVariant    = 0
#countIncorrect  = 0
#countMissingExt = 0
						extension = os.path.splitext(testfile)[1]
						description = magicfixup(magic.from_file(testfile,arg.debug)[0])
#						# Confirm there is an extension on the file
#						if extension:
							# Check extension mapping with type
								# Is Variant
								# Is Incorrect
							# Check extension case
#						else:
							# Is there a DEFAULT case for this description
#							if args.debug: print "Warning: No extension detected for %s" % testfile
			else: 
				countExcluded +=1
				if (args.verbose):
					writeLog(active_log_handles, "%s excluded by subdirectory filter." % (testfile))
				elif (args.debug): print "%s excluded by subdirectory filter." % (testfile))
				else: None
		else: 
			countExcluded +=1
			if (args.verbose):
				writeLog(active_log_handles, "%s excluded by path filter." % (testfile))
			elif (args.debug): print "%s excluded by path filter." % (testfile))
			else: None

# Close temporary report file
if args.reportfile:
	outf.close
else: None

# Do stats calculation
# Create header
# Flush header to report file
# Add rest of report data

#		largest = None
#		count = 0
#		if (len(revextension[description]) > 0):
#			for key in revextension[description]:
#				if revextension[description][key] > count:
#					largest = key 
#					count = revextension[description][key]
#					if args.debug: print "Debug: Marking key %s as the largest (%s) in %s." % (key, count, description)
#				else: None
#			defaultext[description] = {}
#			defaultext[description]['DEFAULT'] = []
#			defaultext[description]['DEFAULT'].append(largest)
#		else:
#			if args.debug: print "Info: There is only one extension, %s, for description, %s." % (key, description)
#	# Write out defaultext
#	try:
#		outf = open(os.path.abspath(args.defaultdictf), 'w')
#	except IOError:
#		if args.debug: print "Error: Cannot write defaultext dict to %." % (os.path.abspath(args.defaultdictf))
#	else:
#		outf.write("defaultext = ")
#        	pp = pprint.PrettyPrinter(indent=1,stream=outf)
#        	pp.pprint(defaultext)
#        	outf.close
#else: None
#
## Merge the defaultext to revextension
#for description in revextension:
#	if description in defaultext.keys():
#		revextension[description].update(defaultext[description])
#	else: None
#
## Write out revextension
#try:
#	outf = open(os.path.abspath(args.revdictf), 'w')
#except IOError:
#	if args.debug: print "Error:  Cannot write revextension dict to %." % (os.path.abspath(args.revdictf))
#else:
#	outf.write("revextension = ")
#	pp = pprint.PrettyPrinter(indent=1,stream=outf)
#	pp.pprint(revextension)
#	outf.close
#
