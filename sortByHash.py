#!/opt/local/bin/python3
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

## Move to commmon
#def delete_file(filename, trash_folder = None, actionfile = None):
#  if trash_folder:
#    basedir = os.path.dirname(filename)
#    trash_folder_pathed = os.path.join(basedir, trash_folder)
#    if os.path.isdir(trash_folder_pathed):
#      if not os.access(trash_folder_pathed, os.W_OK):
#        logger.error("Cannot write to trash folder %s" % trash_folder_pathed)
#        sys.exit(1)
#    else:
#      try:
#        os.makedirs(trash_folder_pathed, exist_ok=True)
#      except:
#        logger.error("Cannot create trash folder %s" % trash_folder_pathed)
#        sys.exit(1)
#      # Action statement
#      if actionfile:
#        actionfile.write("\n")
#        actionfile.write("Date: %s\n" % str(time.time()) )
#        actionfile.write("Action: CreateDir\n")
#        actionfile.write("Object: %s\n" % trash_folder_pathed)
#    existing_file = os.path.join(trash_folder_pathed, os.path.basename(filename))
#    if os.path.isfile(existing_file):
#      logger.error("Would overwrite exsiting file in Trash folder. Please remove content in Trash folder.")
#      sys.exit(1)  
#    try:
#      shutil.move(filename,trash_folder_pathed)
#    except:
#      logger.error("Cannot move file %s to trash folder %s" % (filename, trash_folder_pathed))
#      sys.exit(1)
#    if actionfile:
#      actionfile.write("\n")
#      actionfile.write("Date: %s\n" % str(time.time()) )
#      actionfile.write("Action: MoveFile\n")
#      actionfile.write("Object: %s\n" % filename)
#      actionfile.write("Destination: %s\n" % existing_file)
#  else:
#    try:
#      os.remove(filename)
#    except:
#      logger.error("Cannot remove file %s" % filename) 
#      sys.exit(1)
#    if actionfile:
#      actionfile.write("\n")
#      actionfile.write("Date: %s\n" % str(time.time()) )
#      actionfile.write("Action: DeleteFile\n")
#      actionfile.write("Object: %s\n" % filename)
#       
## Move to commmon
#def move_file(fromfile, tofile, actionfile):
#  if os.path.isfile(tofile):
#    logger.error("Move of %s would overwrite existing file %s." % (fromfile, tofile))
#    sys.exit(1)
#  else:
#    try:
#      shutil.move(fromfile,tofile)
#    except:
#      logger.error("Cannot move file %s to file %s" % (fromfile, tofile)) 
#      sys.exit(1)
#    if actionfile:
#      actionfile.write("\n")
#      actionfile.write("Date: %s\n" % str(time.time()) )
#      actionfile.write("Action: MoveFile\n")
#      actionfile.write("Object: %s\n" % fromfile)
#      actionfile.write("Destination: %s\n" % tofile)
#

# Globals
sourcelist = []
hashes = {}
hashes_sizes = {} # This assumes the hashes come from files of the same size, but close enough for now.

# Parser setup
parser = argparse.ArgumentParser(description='Calculate file hashes and display files collation by hash.')
parser.add_argument('-c', dest='count', type=int, default=0, help='Display only for hash matches of this count or greater.')
parser.add_argument('-s', dest='sizes', action='store_true', default=False, help='Sort by size (high to low), not hash value.')
parser.add_argument('-R', dest='recurse', action='store_true', default=False, help='Recurse into matching directories.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('items', nargs=argparse.REMAINDER, help='List of files or directories (when recurse is set).')


# True out arg parser
args = parser.parse_args()

# Check for arguments/items
print(len(args.items))
if len(args.items) < 1:
  print("Error: One or more items are required")
  sys.exit(1)

# If any of the source args are a directory, then make sure the recurse argument is set
for item in args.items:
  if os.path.isdir(item):
    if not args.recurse:
      print("Warning: One or more source items were directories, and recursion was not set. The directory and its contents will not be included.")
      break
  elif not os.path.isfile(item):
    print("Error: Source item %s not found" % item)
    sys.exit(1)

# Walk the tree as required
for item in args.items:
  print(item)
  print(os.path.isdir(item))
  if os.path.isfile(item):
    sourcelist.append(item)
  elif os.path.isdir(item):
    if args.recurse:
      for root, dirs, files in os.walk(item):
        if args.debug:
          print("root: %s, dirs: %s, files: %s" % (root, dirs, files))
        for f in files:
          sourcelist.append(os.path.join(root,f))
  # Hacky hackness
    elif item == '.' or item == '*': 
      if item == '*':
        item = '.'
      for f in os.listdir(os.path.normpath(item)):
        if args.debug:
          print("item: %s, file: %s" % (os.path.normpath(item), f))
        if os.path.isfile(os.path.join(os.path.normpath(item),f)):
          sourcelist.append(os.path.join(os.path.normpath(item),f))

if args.debug:
  print("Sourcelist:")
  print(sourcelist)

for sourcefile in sourcelist:
# Hash the file
  if os.path.isfile(sourcefile):
    sourcefilesum = cksum(sourcefile)
    if not sourcefilesum:
      print("Warning: File %s can't be hashed. Skipping..." % sourcefile)
      continue
    else:
# Add the file to to the hashes dict
      if sourcefilesum in hashes.keys():
        hashes[sourcefilesum].append(sourcefile)
      else:
        hashes[sourcefilesum] = [sourcefile]
      hashes_sizes[sourcefilesum]=os.path.getsize(sourcefile) # Only size for last file scanned. Meh for now.

  else:
    print("Warning: File %s can't be read. Skipping..." % sourcefile)

if args.sizes:
  sorted_size_hashes = sorted(hashes_sizes.items(), key=lambda x: x[1], reverse=True)
  sorted_hashes = []
  print(sorted_size_hashes)
  for hash in sorted_size_hashes:
    sorted_hashes.append(hash[0]) # Strip tuple
  print(sorted_hashes)
else:
  sorted_hashes = sorted(hashes.keys())

for hash in sorted_hashes:
  if not args.count:
    # Repeat A
    print(hash, ":")
    if args.sizes:
      print("(size:", hashes_sizes[hash], ")")
    for sourcefile in sorted(hashes[hash]):
      print("  ", sourcefile)
  else:
    if len(hashes[hash]) >= int(args.count):
      # Repeat B
      print(hash, ":")
      if args.sizes:
        print("(size:", hashes_sizes[hash], ")")
      for sourcefile in sorted(hashes[hash]):
        print("  ", sourcefile)

print("DONE.")

