import argparse
import os
import magic
# brew install libmagic
# via pip install python-magic
# export PYTHONPATH=/usr/local/lib/python2.7/site-packages

parser = argparse.ArgumentParser(description='Build a list of file extensions and Magic description')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out')
parser.add_argument('-p', dest='path', required=True, help='Root path to build list')
parser.add_argument('-o', dest='filename', required=True, help='Output filename for list')

# True out arg parser
args = parser.parse_args()
if args.debug: print(args)

# Open output file
outf = open(args.filename, 'w')

# Walk the tree and write out line
for root, dirs, files in os.walk(args.path):
	for file in files:
		testfile =  os.path.join(root, file)
		if os.access(testfile, os.R_OK):
			extension = os.path.splitext(testfile)[1]
			if extension:
				#print extension.strip('.')
				#print magic.from_file(testfile).split(',')[0]
				#print magic.from_file(testfile, mime=True)
				# Extension <tab> Mime Type <tab> Magic Description <tab> Full filename
				outf.write(extension.strip('.').lower())
				outf.write('\t')
				outf.write(magic.from_file(testfile).split(',')[0])
				outf.write('\t')
				outf.write(magic.from_file(testfile, mime=True))
				outf.write('\t')
				outf.write(testfile)
				outf.write('\n')
			else:
				if args.debug: print "Warning: No extension detected for %s" % testfile
		else:
			if args.debug: print "ERROR: Can't read file %s" % testfile

# Close output filehandle
outf.close
