#!/opt/local/bin/python3

# Starts with:
# 'Copy of '
# 'Copy \(\d*\) of ')

# Contains:
# .Id_4300359724. or .Id_NN - .Id_NNNNNNNNNNNNNN

# Ends with:
# ' copy' 
# ' copy N'
# -(NNNNN)   

import argparse
import errno
import hashlib
import os
import pprint
import re
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

# Parser setup
parser = argparse.ArgumentParser(description='Looks for duplicate files and remove the duplicate if a source is found.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('items', nargs='+', default=None)

# True out arg parser
args = parser.parse_args()

# Exspand argument list
for item in args.items:
  if item == '*':
    if len(args.items) > 1:
      print("Error: Cannot mix and escaped * and other arguments")
      sys.exit(1)
    else:
      args.items=[]
      for root, dirs, files in os.walk(os.getcwd()):
        for f in files:
          args.items.append(os.path.join(root,f))

for item in args.items:
  if args.debug:
    print(item)
  done = False
  original = item
  original_sum = cksum(item)
  while not done:
    if '.Id_' in item:
      itemtest = re.sub(r'\.Id_[0-9]+\.', '.', item)
      if original == itemtest:
        print("Warning: Regex failed in .Id_")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("Original: %s" % original )
            print("Original: %s" % original_sum )
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
        else:
          item = itemtest
          continue  
    elif 'blah' in item:
      done = True
    else:
      done = True
#for sourcefile in sourcelist:
#  if args.debug: print("Sourcefile: %s" % sourcefile)
#  destfile = os.path.join(args.dest,sourcefile)
#  if args.debug: print("Destfile: %s" % destfile)
#  # Check to see if the source and and woudl be destination file are the physiclaly same
#  if os.path.realpath(sourcefile) == os.path.realpath(destfile):
#    if args.verbose or args.debug: print("Warning: File %s is the same is the intended destination. Skipping..." % sourcefile)
#  else:
#    if os.path.isdir(destfile):
#      print("Warning: File %s can't overwrite a directory. Skipping..." % sourcefile)
#    else:
#      # Else, If destination exsts 
#      if os.path.isfile(destfile):
#        sourcefilesum = cksum(sourcefile)
#        if not sourcefilesum:
#          print("Warning: File %s can't be read. Skipping..." % sourcefile)
#          continue
#        else:
#          if args.debug: print("Sourcefilesum: %s" % sourcefilesum)
#        destfilesum = cksum(destfile)
#        if not destfilesum:
#          print("Warning: File %s can't be read. Skipping..." % sourcefile)
#          continue
#        else:
#          if args.debug: print("Destfilesum: %s" % destfilesum)
#        # If the sums are the same
#        if sourcefilesum == destfilesum:
#          if args.opposite:
#            # Remove destination file
#            if args.verbose or args.debug: print("%s --X %s" % (sourcefile,destfile))
##            os.remove(destfile)
#          else:
#            # Remove source file
#            if args.verbose or args.debug: print("%s X-- %s" % (sourcefile,destfile))
##            os.remove(sourcefile)
#        else:
#          # They didn't match, do nothing
#          if args.verbose or args.debug: print("%s --- %s" % (sourcefile,destfile)) 
#      else:
#      # Otherwise destination doesn't exist
#        # Create folder tree (if needed)
#        if not os.path.isdir(os.path.dirname(destfile)):
#          mkdir_p(os.path.dirname(destfile))
#        # Move file
#        if args.verbose or args.debug: print("%s --> %s" % (sourcefile,destfile))
#
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
