#!/usr/bin/python3
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

# Move to commmon
def delete_file(filename, trash_folder = None, actionfile = None):
  if trash_folder:
    basedir = os.path.dirname(filename)
    trash_folder_pathed = os.path.join(basedir, trash_folder)
    if os.path.isdir(trash_folder_pathed):
      if not os.access(trash_folder_pathed, os.W_OK):
        logger.error("Cannot write to trash folder %s" % trash_folder_pathed)
        sys.exit(1)
    else:
      try:
        os.makedirs(trash_folder_pathed, exist_ok=True)
      except:
        logger.error("Cannot create trash folder %s" % trash_folder_pathed)
        sys.exit(1)
      # Action statement
      if actionfile:
        actionfile.write("\n")
        actionfile.write("Date: %s\n" % str(time.time()) )
        actionfile.write("Action: CreateDir\n")
        actionfile.write("Object: %s\n" % trash_folder_pathed)
    existing_file = os.path.join(trash_folder_pathed, os.path.basename(filename))
    if os.path.isfile(existing_file):
      logger.error("Would overwrite exsiting file in Trash folder. Please remove content in Trash folder.")
      sys.exit(1)  
    try:
      shutil.move(filename,trash_folder_pathed)
    except:
      logger.error("Cannot move file %s to trash folder %s" % (filename, trash_folder_pathed))
      sys.exit(1)
    if actionfile:
      actionfile.write("\n")
      actionfile.write("Date: %s\n" % str(time.time()) )
      actionfile.write("Action: MoveFile\n")
      actionfile.write("Object: %s\n" % filename)
      actionfile.write("Destination: %s\n" % existing_file)
  else:
    try:
      os.remove(filename)
    except:
      logger.error("Cannot remove file %s" % filename) 
      sys.exit(1)
    if actionfile:
      actionfile.write("\n")
      actionfile.write("Date: %s\n" % str(time.time()) )
      actionfile.write("Action: DeleteFile\n")
      actionfile.write("Object: %s\n" % filename)
       
# Move to commmon
def move_file(fromfile, tofile, actionfile):
  if os.path.isfile(tofile):
    logger.error("Move of %s would overwrite existing file %s." % (fromfile, tofile))
    sys.exit(1)
  else:
    try:
      shutil.move(fromfile,tofile)
    except:
      logger.error("Cannot move file %s to file %s" % (fromfile, tofile)) 
      sys.exit(1)
    if actionfile:
      actionfile.write("\n")
      actionfile.write("Date: %s\n" % str(time.time()) )
      actionfile.write("Action: MoveFile\n")
      actionfile.write("Object: %s\n" % fromfile)
      actionfile.write("Destination: %s\n" % tofile)


# Globals
sourcelist = []

# Parser setup
parser = argparse.ArgumentParser(description='Move files that only match the name and checksum of the destination. Useful for merging similar directory structures without loosing unique data.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-o', dest='opposite', action='store_true', default=False, help='If the file is the same, remove the DEST version of the file.') 
parser.add_argument('-R', dest='recurse', action='store_true', default=False, help='Recurse into matching directories.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('-t', dest='test', action='store_true', default=False, help='Test and display the intended operation, but do not actually perform the operations on disk.')
parser.add_argument('-ntrash', dest='trash', action='store_const', const=None, default='__Trash',  help='Disable use of Trash folder.')
parser.add_argument('items', nargs=argparse.REMAINDER)


# True out arg parser
args = parser.parse_args()

# Check for arguments in source and dest
if len(args.items) < 2:
  print("Error: One or more source arguments and one destination argument are required")
  sys.exit(1)
args.dest = os.path.abspath(args.items.pop())

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
    print("Error: Source item %s not found" % item)
    sys.exit(1)

# Walk the tree as required
for item in args.items:
  if os.path.isfile(item):
    sourcelist.append(item)
  elif os.path.isdir(item):
    if args.recurse:
      for root, dirs, files in os.walk(item):
        if args.debug:
          print("root: %s, dirs: %s, files: %s" % (root, dirs, files))
        for f in files:
          sourcelist.append(os.path.join(root,f))
if args.debug:
  print("Sourcelist:")
  print(sourcelist)

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
            if not args.test:
              try:
                if args.trash:
                  delete_file(destfile, args.trash)
                else:
                  os.remove(destfile)
              except:
                print("Warning: Could not remove destination file %s." % destfile)
          else:
            # Remove source file
            if args.verbose or args.debug: print("%s X-- %s" % (sourcefile,destfile))
            if not args.test:
              try:
                if args.trash:
                  delete_file(os.path.abspath(sourcefile), args.trash)
                else:
                  os.remove(os.path.abspath(sourcefile))
              except:
                print("Warning: Could not remove source file %s." % sourcefile)
        else:
          # They didn't match, do nothing
          if args.verbose or args.debug: print("%s --- %s" % (sourcefile,destfile)) 
      else:
      # Otherwise destination doesn't exist
        # Create folder tree (if needed)
        if not os.path.isdir(os.path.dirname(destfile)):
          if not args.test:
            try:
              mkdir_p(os.path.dirname(destfile))
            except:
              print("Warning: Could not create directory %s." % os.path.dirname(destfile))
        # Move file
        if args.verbose or args.debug: print("%s --> %s" % (sourcefile,destfile))
        if not args.test:
          move_file(os.path.abspath(sourcefile), os.path.abspath(destfile), None)

print("DONE.")

