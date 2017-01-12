#!/usr/bin/python
import argparse
import os
import magic
# brew install libmagic
# via pip install python-magic
# export PYTHONPATH=/usr/local/lib/python2.7/site-packages
import re
import stat
from magicfixup import magicfixup

# Don't navigate these root paths
exclude_paths = ['/dev','/tmp','/Volumes']

parser = argparse.ArgumentParser(description='Build a list of file extensions and Magic description')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out')
parser.add_argument('-p', dest='path', required=True, help='Root path to build list')
parser.add_argument('-o', dest='filename', required=True, help='Output filename for list')

# Ok to process based on exlude list
def excludeCheckPassed(checkfile, myList):
	for x in myList:
		regex = '^' + re.escape(x)
		if re.search(regex,checkfile):
			if args.debug: print "Warning: Skipping file %s since path %s is in the exclude list" % (checkfile,x)
        		return False
		else:
			None
	return True

# True out arg parser
args = parser.parse_args()
if args.debug: print(args)

# Open output file
outf = open(args.filename, 'w')

# Walk the tree and write out line
for root, dirs, files in os.walk(args.path):
	for file in files:
		testfile =  os.path.join(root, file)
		# Check for excluded paths
		if excludeCheckPassed(testfile,exclude_paths):
			# Check for a symlink which messes with the socket check
			if os.path.islink(testfile):
				if args.debug: print "Warning: Skipping file %s since it is a symlink" % testfile
			else:
				# Readable as the current user
				try:
					fp = open(testfile,'r')
				except IOError:
					if args.debug: print "Error: Skipping file %s due to access perimissions" % testfile
					next
				else:
					fp.close
				        # Checking to see if file is a socket
        				mode = os.stat(testfile).st_mode
        				if stat.S_ISSOCK(mode):
        					if args.debug: print "Warning: Skipping file %s since it is a socket" % testfile
        				else:   
						extension = os.path.splitext(testfile)[1]
						# Confirm there is an extension on the file
						if extension:
							# Cleanup description to strip out per-file data
							description = magicfixup(magic.from_file(testfile,arg.debug).split(',')[0])
							# Write out data: Extension <tab> Mime Type <tab> Magic Description <tab> Full filename
							outf.write(extension.strip('.').lower())
							outf.write('\t')
							outf.write(description)
							outf.write('\t')
							outf.write(magic.from_file(testfile, mime=True))
							outf.write('\t')
							outf.write(testfile)
							outf.write('\n')
						else:
							if args.debug: print "Warning: No extension detected for %s" % testfile
		else:
			None

# Close output filehandle
outf.close
