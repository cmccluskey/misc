#!/opt/local/bin/python3
#sys.path.append("/usr/local/lib/python2.7/site-packages")
import argparse
import errno
import hashlib
import os
import shutil 
import sys


def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: 
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

def cksum(filename):
  BLOCKSIZE = 65536
  hasher = hashlib.sha1()
  try:
    with open(filename, 'rb') as afile:
      buf = afile.read(BLOCKSIZE)
      while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(BLOCKSIZE)
  except:
    return None
  return hasher.hexdigest()

# Globals
sourcelist = []

# Parser setup
parser = argparse.ArgumentParser(description='Move files that only match the name and checksum of the destination. Useful for merging similar directory structures without loosing unique data.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-o', dest='opposite', action='store_true', default=False, help='If the file is the same, remove the DEST version of the file.') 
parser.add_argument('-r', dest='recurse', action='store_true', default=False, help='Recurse into matching directories.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('items', nargs='+', default=None)

# True out arg parser
args = parser.parse_args()

# Check for arguments in source and dest
if len(args.items) < 2:
  print("Error: One or more source arguments and one destination argument are required")
  sys.exit(1)
args.dest = args.items.pop()

# If there a muliple source arguments then the dest needs to be an existing directory
if len(args.items) > 1:
  if not os.path.isdir(args.dest):
    print("Error: With multiple source arguments, the destination must be a directory")
    sys.exit(1)

# If any of the source args are a directory, then make sure the recurse argument is set
for item in args.items:
  if os.path.isdir(item):
    if not args.recurse:
      print("Warning: One or more source items were drectories, and recursion was not set. The directory and its contents will not be included.")
      break
  elif not os.path.isfile(item):
    print("Error: Source item %s not found", item)
    sys.exit(1)

# Walk the tree as required
for item in args.items:
  if os.path.isfile(item):
    sourcelist.append(item)
  elif os.path.isdir(item):
    if args.recurse:
      for root, dirs, files in os.walk(item):
#        print("root: %s, dirs: %s, files: %s" % (root, dirs, files))
        for f in files:
          sourcelist.append(os.path.join(root,f))
# print(sourcelist)

for sourcefile in sourcelist:
  if args.debug: print("Sourcefile: %s" % sourcefile)
  destfile = os.path.join(args.dest,sourcefile)
  if args.debug: print("Destfile: %s" % destfile)
  # Check to see if the source and and woudl be destination file are the physiclaly same
  if os.path.realpath(sourcefile) == os.path.realpath(destfile):
    if args.verbose or args.debug: print("Warning: File %s is the same is the intended destination. Skipping..." % sourcefile)
  else:
    if os.path.isdir(destfile):
      print("Warning: File %s can't overwrite a directory. Skipping..." % sourcefile)
    else:
      # Else, If destination exsts 
      if os.path.isfile(destfile):
        sourcefilesum = cksum(sourcefile)
        if not sourcefilesum:
          print("Warning: File %s can't be read. Skipping..." % sourcefile)
          continue
        else:
          if args.debug: print("Sourcefilesum: %s" % sourcefilesum)
        destfilesum = cksum(destfile)
        if not destfilesum:
          print("Warning: File %s can't be read. Skipping..." % sourcefile)
          continue
        else:
          if args.debug: print("Destfilesum: %s" % destfilesum)
        # If the sums are the same
        if sourcefilesum == destfilesum:
          if args.opposite:
            # Remove destination file
            if args.verbose or args.debug: print("%s --X %s" % (sourcefile,destfile))
#            os.remove(destfile)
          else:
            # Remove source file
            if args.verbose or args.debug: print("%s X-- %s" % (sourcefile,destfile))
#            os.remove(sourcefile)
        else:
          # They didn't match, do nothing
          if args.verbose or args.debug: print("%s --- %s" % (sourcefile,destfile)) 
      else:
      # Otherwise destination doesn't exist
        # Create folder tree (if needed)
        if not os.path.isdir(os.path.dirname(destfile)):
          mkdir_p(os.path.dirname(destfile))
        # Move file
        if args.verbose or args.debug: print("%s --> %s" % (sourcefile,destfile))
#        try:
#          shutil.move(sourcefile, destfile)
#        except:
#          print("Error: Unable to move %s to %s." % (sourcefile,destfile))

print("DONE.")


#					($filename eq '.') ||
#					($filename eq '..') ||
#					(-l $long_filename) ||
#					# End of UNIX system exceptions
#					($filename eq 'proc') ||
#					($filename eq '.AppleDesktop') ||
#					($filename eq '.AppleDouble') || 
#					($filename eq '.finderinfo') || 
#					($filename eq '.resource') || 
#					($filename eq '.xvpics') ||
#					# End of UNIX userspace exceptions
#					($filename =~ /recycled/i) || 
#					# End of Win userspace exceptions
#                                       ($filename eq '.DS_Store')
#                                       # End of OSX userspace exceptions
