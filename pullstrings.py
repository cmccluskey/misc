#!/usr/bin/python
import sys
sys.path.append("/usr/local/lib/python2.7/site-packages")
import argparse
import os
import re
import subprocess
#import stat
#import magic
# brew install libmagic
# via pip install python-magic
# export PYTHONPATH=/usr/local/lib/python2.7/site-packages
#from magicfixup import magicfixup
#from datetime import datetime

# Temporary file extension
temp_ext        = ".tmp"

# Parser setup
parser = argparse.ArgumentParser(description='Given a file of filenames, search for strings, and sort output.')
parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-o', dest='outfile', default=False, help='Output the sorted data to this file.')
parser
parser.add_argument('-i', dest='infile', default=False, help='Read this list of files from this file.') 
parser.add_argument('-s', dest='strings_exec', default='/usr/bin/strings', help='Override the full path to the strings binary.')
parser.add_argument('-g', dest='grep_exec', default='/bin/grep', help='Override the full path to the egrep-compatible grep binary.') 


# True out arg parser
args = parser.parse_args()

# Make sure one of the primary validation modes is set
if (not args.infile or not args.outfile ):
  parser.print_help()
  print "\n"
  print "Error: Need both the infile and the outfile supplied."
  sys.exit(1)
else: None

if not os.access(args.strings_exec, os.X_OK):
  print "Error: Supplied path to strings was not found/executable."
  sys.exit(1)

if not os.access(args.grep_exec, os.X_OK):
  print "Error: Supplied path to grep was not found/executable."
  sys.exit(1)

include_strings = ['madam', 'bookmark', 'chris', 'mcclusk', 'vidch', 'tekno', 'technodude']
exclude_strings = ['wChk', 'checkbox', 'checkboxes', 'checkmark', 'Christmas', 'checkerboard', 'checksum type %s', 'check slice %s', 'checkDisk:withFormat:', 'Christopher Moore', 'check-am: all-am', 'check: check-am', 'BookmarksSearchBar', 'mADAM']
exclude_fuzzy = ['Christmas Island', 'christian', 'ports-supfile', 'ng_one2many.ko', 'Christopher Aillon', 'Christoph Wickert', 'Christoph Maser', 'Christian Persch', 'Chris Weyl', 'Christof Damian', 'Christopher Meng', 'Christoph Ganser', 'Chris Feist', 'ChristmasIsland', 'Chris Botti', 'Chris Lumens', 'Schaller']

# Open input fileq
if args.infile:
  try:
    inf = open(os.path.abspath(args.infile))
  except IOError:
    print "Error: Cannot open inputfile %s for reading." % (args.infile)
    sys.exit(1)

# Open output file
if args.outfile:
  try:
    outf = open(os.path.abspath(args.outfile), 'w')
  except IOError:
    print "Error: Cannot open outfile %s for writing." % (args.outfile)
    sys.exit(1)

# Prep "grep"
search_re_string = '|'.join(include_strings)
search_re = re.compile(search_re_string, re.IGNORECASE)

# Get next test file from the input file
for tfile in inf:
  tfile = tfile.strip('\n')
  tfile_full = os.path.abspath(tfile)
  if os.access(tfile_full, os.R_OK):
# Get strings
    strings_buffer = subprocess.check_output([args.strings_exec, tfile_full])
    strings = strings_buffer.split('\n')
# Grep through strings and put matches into an array
    matches = []
    for possible in strings:
      if search_re.match(possible):
        matches.append(possible)
# Remove duplicates in the array and remove the excludes
    matches = list(set(matches) - set(exclude_strings))
# Futher filter with other case insentisitve matches
    for item in matches:
      for searchitem in exclude_fuzzy:
        search_re_again = re.compile(searchitem, re.IGNORECASE)
        if search_re_again.match(item):
          matches.remove(item)
# Sort the array
    matches.sort()
# If the size of the array > 0
    if len(matches) > 0:
## Print the file + <CRLF>
      outf.write("%s\n" % tfile)
## For each item in the array
      for match in matches:
### Print a # and then the string and then <CRLF>
        outf.write("# %s\n" % match)
      outf.flush()
  else:
    print "Error: Cannot read test file %s" % tfile_full

# Close the output file
if outf:
	outf.flush()
	outf.close()

# Close the input file
if inf:
        inf.close()
