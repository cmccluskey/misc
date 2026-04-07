#!/opt/local/bin/python3
import argparse
import errno
import hashlib
import os
import shutil 
import signal
import sys
import time

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
sizes = {}

# Parser setup
parser = argparse.ArgumentParser(description='Calculate file hashes and display files collation by hash.')
parser.add_argument('-c', dest='count', type=int, default=0, help='Display only for hash matches of this count or greater.')
parser.add_argument('-R', dest='recurse', action='store_true', default=False, help='Recurse into matching directories.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('items', nargs=argparse.REMAINDER, help='List of files or directories (when recurse is set).')


# True out arg parser
args = parser.parse_args()

# Check for arguments/items
if len(args.items) < 1:
  print("Error: One or more items are required")
  sys.exit(1)

# If any of the source args are a directory, then make sure the recurse argument is set
for item in args.items:
  if os.path.isdir(item):
    if not args.recurse:
      print("Warning: One or more source items were directories, and recursion was not set. Only the content of the directory included.")
      break
  elif not os.path.isfile(item):
    print("Error: Source item %s not found" % item)
    sys.exit(1)

if args.debug:
  print("items:")
  print(args.items)

# Walk the tree as required
for item in args.items:
  if os.path.isfile(item):
    sourcelist.append(item)
  elif os.path.isdir(item):
    for root, dirs, files in os.walk(item):
      if args.debug:
        print("root: %s, dirs: %s, files: %s" % (root, dirs, files))
      for f in files:
        sourcelist.append(os.path.join(root,f))
      if not args.recurse:
        break
  else:
    print("Warning: Supplied path or object %s can't be found. Skipping..." % item)   
#  # Hacky hackness
#    elif item == '.' or item == '*': 
#      if item == '*':
#        item = '.'
#      for f in os.listdir(os.path.normpath(item)):
#        if args.debug:
#          print("item: %s, file: %s" % (os.path.normpath(item), f))
#        if os.path.isfile(os.path.join(os.path.normpath(item),f)):
#          sourcelist.append(os.path.join(os.path.normpath(item),f))
  
if args.debug:
  print("Sourcelist:")
  print(sourcelist)
  
for sourcefile in sourcelist:
# Get sizes of file 
  if os.path.isfile(sourcefile):
    sourcefilesize = os.path.getsize(sourcefile)
    if not sourcefilesize:
      print("Warning: File %s can't be hashed. Skipping..." % sourcefile)
      continue
    else:
# Add the file to to the sizes dict
      if sourcefilesize in sizes.keys():
        sizes[sourcefilesize].append(sourcefile)
      else:
        sizes[sourcefilesize] = [sourcefile]
  else:
    print("Warning: File %s can't be read. Skipping..." % sourcefile)
  
for sz in sorted(sizes.keys(), reverse=True):
  hashes = {}
  if len(sizes[sz]) >= int(args.count):
    for sourcefile in sizes[sz]:
    # Hash the file
      sourcefilesum = cksum(sourcefile)
      if not sourcefilesum:
        print("Warning: File %s can't be hashed. Skipping..." % sourcefile)
        continue
      else:
        if sourcefilesum in hashes.keys():
          hashes[sourcefilesum].append(sourcefile)
        else:
          hashes[sourcefilesum] = [sourcefile]
  if not args.count:
    # No pair, and so no hash
    print(sz,"B:")
    for sourcefile in sorted(sizes[sz]):
      print("  ", sourcefile)
  else:
    for hash in hashes:
      if len(hashes[hash]) >= int(args.count):
        # The hash has files that are greater than count
        print(sz,"B, Hash: ",hash,":")
        for sourcefile in sorted(sizes[sz]):
          print("  ", sourcefile)

print("DONE.")
