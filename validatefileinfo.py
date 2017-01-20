#!/usr/bin/python
import sys
sys.path.append("/usr/local/lib/python2.7/site-packages")
import argparse
import os
import re
import stat
import magic
# brew install libmagic
# via pip install python-magic
# export PYTHONPATH=/usr/local/lib/python2.7/site-packages
from magicfixup import magicfixup
from datetime import datetime


# Counters
countTotal      = 0 # Scanned plus all no-scan cases
countScanned    = 0 # Scanned cases total (see below)
countNoAccess   = 0 # Unscanned
countSkipped    = 0 # Unscanned
countExcluded   = 0 # Unscanned
countSymLink    = 0 # No real file

# Counters of scanned items
countCorrect    = 0 # All is good
countCase       = 0 # Extension case was messed up
countVariant    = 0 # Proper variant of extension
countIncorrect  = 0 # Invalid extension noted
countMissingExt = 0 # No extension
countMissingDesc= 0 # No descrition entry 

# Timers
startTime       = datetime.now()
endTime         = 0

# Temporary file extension
temp_ext        = ".tmp"

# Ok to process based on exlude list
def excludeRootCheckPassed(checkfile, myList):
	checkfile = os.path.dirname(checkfile)
	for x in myList:
		regex = '^' + re.escape(x)
		if re.search(regex,checkfile):
			return False
		else: None
	return True

def excludeDirCheckPassed(checkfile, myList):
	checkfile = os.path.dirname(checkfile)
	for x in myList:
        	regex = re.escape(x)
		if re.search(regex,checkfile):
			return False
		else: None
	return True

def changeCase(filename, extension, case, extdict):
	(path, strippedfile, strippedext) = fileParts(filename)
	if ( case == 'lower'):
		strippedext = strippedext.lower()
	elif (case == 'upper'):
		strippedext = strippedext.upper()
	elif (case == 'stored'):
		if (extdict['DEFAULT'][0]):
			strippedext = extdict['DEFAULT'][0]
		else:
			strippedext = extension
	else: None
	returnfile = path + '/' + strippedfile + '.' + strippedext
	if (args.debug): print "changeCase: returnfile: %s" % returnfile
	return (returnfile)

def changeExt(filename, extension, case, extdict = {}):
	(path, strippedfile, strippedext) = fileParts(filename)
	filename = path + '/' + strippedfile + '.' + extension
	filename = changeCase(filename, extension, case, extdict)
	if (args.debug): print "changeExt: filename: %s" % filename
	return filename

def writeLog(handles, line):
	for handle in handles:
		handle.write(line)
		handle.write('\n')
	return True

def fileParts(filename):
	(path, fileproper) = os.path.split(filename)
	if '.' in fileproper:
		(base, extension) = fileproper.rsplit('.',1)
	else:
		base = fileproper
		extension = ''
	if (args.debug): print "fileParts: %s %s %s" % (path, base, extension)
	return [path, base, extension]

# Parser setup
parser = argparse.ArgumentParser(description='Validate files and thier extensions based on Magic description. Either report, rewrite, or move files that don\'t conform to the dictionary.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-e', dest='revextdict', default='./dicts/revextension.dict', help='Override the location of the extension dictionary.') 
parser.add_argument('-p', dest='path', required=True, help='Root path to start validation run.')
parser.add_argument('-C', dest='case', default='lower', nargs=1, choices=['upper','lower','stored'], help='Specify case (default lower).')
parser.add_argument('-r', dest='reportfile', default=False, help='Enable a report, and store the report at this location. If run without other operation, only the report of what would be done will be written.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Normally skipped, unavailable, and ok files are not written to the report, this enables those entries in the report.') 
parser.add_argument('-c', dest='caserun', action='store_true', default=False, help='Perform a modify case run.')
parser.add_argument('-m', dest='moverun', default=False, help='Perform a moving run by specififying a destination subdirectory relative to the current filename. You can provide a full path to move to a set location.')
parser.add_argument('-n', dest='namerun', action='store_true', default=False, help='Perform a rename-in-place run, modifying the suffix and case in place.')
parser.add_argument('-0', dest='addextension', action='store_true', default=False, help='Add an extension, if DEFAULT is found, for files that don\'t have one. Log entries in report if DEFAULT is not found.')

# True out arg parser
args = parser.parse_args()

# Make sure one of the primary validation modes is set
if not (args.reportfile or args.caserun or args.moverun or args.namerun):
	parser.print_help()
	print "\n"
	print "Error: One of the runtime modes must be to run a report (-r), change the case (-c), move nonconforming files to a directory (-m), to rename in place (-n)."
	sys.exit(1)
else: None

# Make sure that there isn't more than one validation mode set
if ( (args.caserun and args.moverun and args.namerun) or (args.caserun and args.namerun) or (args.caserun and args.moverun) or (args.moverun and args.namerun) ):
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
if args.moverun:
	movedir_clean = args.moverun.rstrip('/')
	if not excludeRootCheckPassed(args.moverun, ['/']):
		movedir_clean = os.path.abspath(movedir_clean)
		exclude_paths.append(movedir_clean)
	else:
		movedir_clean = os.path.basename(movedir_clean)
		exclude_directories.append(movedir_clean)
else: None

# Open report file
if args.reportfile:
	try:
		outf = open(os.path.abspath(args.reportfile + temp_ext), 'w')
	except IOError:
		print "Error: Cannot open reportfile %s for writing." % ((args.reportfile + temp_ext))
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
	inf.close()

# Walk the tree and write out line
for root, dirs, files in os.walk(args.path):
	for file in files:
		countTotal += 1
		# File under test
		testfile =  os.path.join(root, file)
		# Proposed name after case rewrite
		casefile = ''
		# Proposed iterated name change
		modifiedfile = ''
		# Flag to fix the file (used for safety checks)
		needsfixing=False
		# Flag to move the file without fixing name (safety check)
		nomodifiedfile=False
		# Check for excluded paths from root
		if excludeRootCheckPassed(testfile,exclude_paths):
			# Check excluded directories
			if excludeDirCheckPassed(testfile,exclude_directories): 
			# Check for a symlink which messes with the socket check
				if os.path.islink(testfile):
					countSkipped +=1
					if (args.verbose): writeLog(active_log_handles, "%s skipped as a symlink." % (testfile))
					elif (args.debug): print "%s skipped as a symlink." % (testfile)
					else: None
				else:
					# Readable as the current user
					try:
						fp = open(testfile,'r')
					except IOError:
						countNoAccess +=1
						if (args.verbose): writeLog(active_log_handles, "%s skipped due to access permissions." % (testfile))
						elif (args.debug): print "%s skipped due to access permissions." % (testfile)
						else: None
					else:
						fp.close()
						# Checking to see if file is a socket
						mode = os.stat(testfile).st_mode
						if stat.S_ISSOCK(mode):
							countSkipped += 1
							if (args.verbose): writeLog(active_log_handles, "%s skipped as a named socket/pipe." % (testfile))
							elif (args.debug): print "%s skipped as a named socket/pipe." % (testfile)
						else:
							# We are going to Scan this file now
							countScanned += 1
							if (args.debug): print "Testfile: %s" % testfile
							extension = fileParts(testfile)[2]
							if (args.debug): print "Extension: %s" % extension
							description = magicfixup(magic.from_file(testfile), False)
							if (description in revextension):
								# Confirm there is an extension on the file
								if extension:
									# Note a case fault. If we aren't rewriting case, revert the "destination" file back to the original.
									# Future case changes will be done on extension rewrites.			
									casefile = changeCase(testfile, extension, args.case, revextension[description])
									if not (casefile == testfile):
										countCase += 1
										if args.caserun:
											writeLog(active_log_handles, "%s has bad case (%s) and will be changed to %s." % (testfile,args.case,casefile))
											needsfixing=True
										else: 
											# Reverse the change
											casefile = testfile
									else: None
									# Initalize modifiedfile to the output of the casefile
									modifiedfile = casefile
#									print "Casefile: %s" % (casefile)
									# Check extension mapping via description
#									print "Extension:'%s', Keys:%s" % (extension, revextension[description].keys())	
									if ('DEFAULT' in revextension[description].keys()):
										if (extension.lower() == revextension[description]['DEFAULT'][0].lower()):
											# Yes, the extension is correct for the description 
											if (args.verbose): writeLog(active_log_handles, "%s has the correct extension '%s' for '%s'." % (testfile,extension,description))
											elif (args.debug): print "%s has the correct extension '%s' for '%s'." % (testfile,extension,description)
											countCorrect += 1
											nomodifiedfile=True
										else:
											if ('EXCLUDE' in revextension[description].keys()):
												if extension.lower() in revextension[description]['EXCLUDE']:
													if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description))
													elif (args.debug): print "%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description)
													countVariant += 1	
													nomodifiedfile=True
												else:
													writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
													modifiedfile = changeExt(casefile, revextension[description]['DEFAULT'][0], args.case, revextension[description])
													countIncorrect += 1
													needsfixing=True 
											else:
												writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
												modifiedfile = changeExt(casefile, revextension[description]['DEFAULT'][0], args.case, revextension[description])
												countIncorrect += 1
												needsfixing=True
#												if (args.debug): print "Extension Mapping: modifiedfile: %s" % modifiedfile
									# Is a variant
									elif (extension.lower() in revextension[description].keys()):
										# Is this extension EXCLUDED from being rewritten
										if ('EXCLUDE' in revextension[description].keys()):
											if extension.lower() in revextension[description]['EXCLUDE']:
												# In the exclude list, so don't change the file
												if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description))
												elif (args.debug): print "%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description)
											else: None
											countVariant += 1
											nomodifiedfile=True
 										else:
											# Is there a DEFAULT?
											if ('DEFAULT' in revextension[description].keys()):
												# Then move
												writeLog(active_log_handles, "%s has a known extension '%s' for '%s' but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
												modifiedfile = changeExt(casefile, revextension[description]['DEFAULT'][0], args.case, revextension[description])
												countVariant += 1
												needsfixing=True
#												if (args.debug): print "Add Default: modifiedfile: %s" % modifiedfile
											else:
											# There isn't a default, so do nothing
												if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s' and the extension won't be changed." % (testfile,extension,description))
												elif (args.debug): print "%s has a known extension '%s' for '%s' and the extension won't be changed." % (testfile,extension,description)
												else: None
												countVariant += 1
												nomodifiedfile=True
									else:
										# Assuming incorrect extension for description
										countIncorrect += 1
										# Is there an alternate extenstion available?
										if ('DEFAULT' in revextension[description].keys()):
											writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
											modifiedfile = changeExt(casefile, revextension[description]['DEFAULT'][0], args.case, revextension[description])
											needsfixing=True
#											if (args.debug): print "Add Default #2: modifiedfile: %s" % modifiedfile
										else:	
											writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but it's unclear what possible extension to use '%s'." % (testfile,extension,description,revextension[description].keys()))
											needsfixing=True
											nomodifiedfile=True
								else:
									countMissingExt += 1
									modifiedfile=testfile
									casefile=testfile
									if args.addextension:
										if ('DEFAULT' in revextension[description].keys()):
											writeLog(active_log_handles, "%s has no extension, but has a potential default of '%s' for '%s'." % (testfile,revextension[description]['DEFAULT'][0],description))
											if (args.addextension):
												modifiedfile = changeExt(casefile, revextension[description]['DEFAULT'][0], args.case, revextension[description])
												needsfixing=True
												if (args.debug): print "Add Extension: modifiedfile: %s" % modifiedfile
											else: None
										else:
											writeLog(active_log_handles, "%s has no extension, and there is no default extension set for '%s'." % (testfile, description))
									else: None
								# Begin actual fixes here
								# Interlock checks before mucking around with files
								if (modifiedfile == ''):
									print "Error: The destination filename was not specified, and indicates a filter/modification problem."
									print "Testfile: %s\nModified: %s" % (testfile,modifiedfile)
									sys.exit(1)
								else: None
								if (casefile == ''):
									print "Error: The case-changed filename was not specified, and indicates a filter/modification problem."
									print "Testfile: %s\nCasefile: %s" % (testfile,casefile)
									sys.exit(1)
								if needsfixing:
									if (modifiedfile == testfile):
										if not nomodifiedfile:
											print "Error: We have a needsfixing flag with no changes in filename"
											print "Testfile: %s\nModified: %s" % (testfile,modifiedfile)
											sys.exit(1)
										else: 
											None # This indicates a move without changing the name
									else: 
										None # Normal case
									# Now perform one of the run modes
									# Just alter the case of the extension in-place (to casefile)
									if (args.caserun):
										# Make sure the destination file doesn't exit, else throw error and bail for now
										# Move/rename the file to a new case
										None	
									# Move/rename the file to modfied file name in the same location (in-place)
									elif (args.namerun):
										# Make sure the destination doesn't exit, else throw error and bail for now
										# Move/rename the file to a new name
										None
									# Do not modify the file any further, just move the errored file to a global path OR to local (to file) subdirectory
									elif (args.moverun):
										# Global path or local subdirectory move
										# Alter destination file path to compensate
										# Make sure the directory exists, if not create it
										# Make sure the destination doesn't exit, else throw error and bail for now
										# Move/rename the file to a new location without renaming
										None
									else:
										None 
								else:
									if (args.verbose): writeLog(active_log_handles, "No modification of %s required." % (testfile))
									elif (args.debug): print "No modification of %s required." % (testfile)
							else:
								# There is no description found in revextensions
								countMissingDesc += 1
								if (args.verbose): writeLog(active_log_handles, "%s doesn't have a valid description '%s' in the revextension dict." % (testfile,description))
								elif (args.debug): print "%s doesn't have a valid description '%s' in the revextension dict." % (testfile,description)
			else: 
				countExcluded +=1
				if (args.verbose):
					writeLog(active_log_handles, "%s excluded by subdirectory filter." % (testfile))
				elif (args.debug): print "%s excluded by subdirectory filter." % (testfile)
				else: None
		else: 
			countExcluded +=1
			if (args.verbose):
				writeLog(active_log_handles, "%s excluded by path filter." % (testfile))
			elif (args.debug): print "%s excluded by path filter." % (testfile)
			else: None

# Close temporary report file
if args.reportfile:
	outf.flush()
	outf.close()
else: None

#print os.stat(os.path.abspath(args.reportfile + temp_ext)).st_size 

# Do stats calculation
endTime         = datetime.now()
elapsed			= (endTime - startTime).total_seconds()
#print elapsed
filePerSec		= 0.0
filesPerSec    = countTotal / elapsed

# Open temp file
if args.reportfile:
	try:
		tempf = open(os.path.abspath(args.reportfile + temp_ext), 'r')
	except IOError:
		print "Error: Cannot open temp reportfile %s for reading." % (args.reportfile + temp_ext)
		sys.exit(1)
	else: None
else: None

# Open report file for header placement
if args.reportfile:
	try:
		reportf = open(os.path.abspath(args.reportfile), 'w')
	except IOError:
		print "Error: Cannot open reportfile %s for writing." % (args.reportfile)
		sys.exit(1)
	else: None
else: None

if args.reportfile:
	reportf.write("\n")
	reportf.write("Report for files in path: %s\n" % (args.path) )
	reportf.write("\n")
	reportf.write("Report start time: %s\n" % (startTime) )
	reportf.write("Report end time:   %s\n" % (endTime) )
	reportf.write("%s files were processed in total, at a rate of %.2f files per second.\n" % (countTotal, filesPerSec))
	reportf.write("\n")
	reportf.write("%s%s%s Total Count\n" % (str(countTotal).ljust(10), ''.ljust(10), ''.ljust(10)))
	reportf.write("%s%s%s No Access\n" % (''.ljust(10), str(countNoAccess).ljust(10), ''.ljust(10)))
	reportf.write("%s%s%s Skipped\n" % (''.ljust(10), str(countSkipped).ljust(10), ''.ljust(10)))
	reportf.write("%s%s%s Excluded\n" % (''.ljust(10), str(countExcluded).ljust(10), ''.ljust(10)))
	reportf.write("%s%s%s Symlink\n" % (''.ljust(10), str(countSymLink).ljust(10), ''.ljust(10)))
	reportf.write("%s%s%s Scanned\n" % (''.ljust(10), str(countScanned).ljust(10), ''.ljust(10)))
	reportf.write("%s%s%s Correct\n" % (''.ljust(10), ''.ljust(10), str(countCorrect).ljust(10)))
	reportf.write("%s%s%s Acceptable Variant in Extension\n" % (''.ljust(10), ''.ljust(10), str(countVariant).ljust(10)))
	reportf.write("%s%s%s Incorrect Extension\n" % (''.ljust(10), ''.ljust(10), str(countIncorrect).ljust(10)))
	reportf.write("%s%s%s Missing Extension\n" % (''.ljust(10), ''.ljust(10), str(countMissingExt).ljust(10)))
	reportf.write("%s%s%s Missing Description\n" % (''.ljust(10), ''.ljust(10), str(countMissingDesc).ljust(10)))
	reportf.write("%s%s%s Incorrect Case (not included in Scanned Count)\n" % (''.ljust(10), ''.ljust(10), str(countCase).ljust(10)))
	reportf.write("\n\n")
	reportf.write("Data\n")
	reportf.write("__________________________________________\n")
	while True:
		line = tempf.readline()
		if line == '':
			break
		else:
			reportf.write(line)
	reportf.close()
	tempf.close()
else: None

# Delete temp file
os.remove(os.path.abspath(args.reportfile + temp_ext))
