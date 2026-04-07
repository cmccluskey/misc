#!/usr/bin/python3
import argparse
import os
import re
import shutil 
import subprocess
import sys


def get_objects_in_archive(archive=None, unarchiver_spec=None, debug=False):
  default_max_count = sys.maxsize # The biggest int on the block
  object_buffer = []
  return_buffer = []
  result = None

  try: # In text mode, a failure of unicode in the output can cause an issue
    if 'list_args' in unarchiver_spec:
      if unarchiver_spec['list_args']:
        result = subprocess.run([unarchiver_spec['binary'], unarchiver_spec['list_args'], archive], timeout=300, text=True, input='\n\n\n', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if debug:
      print(result)
    return_buffer = result.stdout.splitlines()
    if result.returncode != 0:
      print("WARNING: File list command", unarchiver_spec['binary'], unarchiver_spec['list_args'], archive, "failed. Skipping archive.")
      return object_buffer
    else:
      for line in return_buffer:
        for fname_spec in unarchiver_spec['object_filters']:
          fmatch = re.search(fname_spec, line)
          if fmatch:
            object_buffer.append(fmatch.group(1))
            continue
    return object_buffer
  except Exception as e:
    print("Error: Skipping", archive, "as an extraction error occurred in get_objects_in_archive:", e)
    return object_buffer

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

def octal_dump(text):
  obuffer = []
  for chr in text:
    obuffer.append(oct(ord(chr)))
  return(" ".join(obuffer))


# Globals
sourcelist = []
unarchivers = { 'zip': { 'binary_base': 'unzip', 'binary': '/usr/bin/unzip',       'list_args': '-l', 'version': 'UnZip 6.00 of 20 April 2009, by Info-ZIP',
                         'object_filters': [ '\s{0,}\d{1,}\s{1,}[\d\-]{8,}\s{1,}[\d:]{3,}\s{2,}(.*)$' ] }, 
                'rar': { 'binary_base': 'unrar', 'binary': '/opt/homebrew/bin/unrar', 'list_args': 'l',  'extract_args': 'x', 'version': 'UNRAR 7.11 freeware',
                         'multipart_string': ['part\d\.rar'], 'multipart_base': ['part1\.rar'],
                         'object_filters': [ '\s{1,}[A-Z.]{7,7}\s{1,}\d{1,}\s{1,}[\d\-]{8,}\s{1,}[\d:]{3,}\s{1,}(.*)$',    # Newer RAR 
                                             '\s{1,}[rwx\-]{3,}\s{1,}\d{1,}\s{1,}[\d\-]{8,}\s{1,}[\d:]{3,}\s{1,}(.*)$'     # RAR 1.5 
                                           ] }, 
                'cbr': { 'binary_base': 'unrar', 'binary': '/opt/homebrew/bin/unrar', 'list_args': 'l',  'extract_args': 'x', 'version': 'UNRAR 7.11 freeware',
                         'multipart_string': ['part\d\.cbr'], 'multipart_base': ['part1\.cbr'],
                         'object_filters': [ '\s{1,}[A-Z.]{7,7}\s{1,}\d{1,}\s{1,}[\d\-]{8,}\s{1,}[\d:]{3,}\s{1,}(.*)$',    # Newer RAR
                                             '\s{1,}[rwx\-]{3,}\s{1,}\d{1,}\s{1,}[\d\-]{8,}\s{1,}[\d:]{3,}\s{1,}(.*)$'     # RAR 1.5 
                                           ] },
#               'not': { 'binary_base': 'unnot', 'binary': '/opt/local/bin/unnon', 'list_args': 'l',  'extract_args': 'x', 'version': 'Bogus not 1.234',
#                        'object_filters': '\s{2,}[A-Z.]{7,7}\s{2,}\d{1,}\s{2,}[\d\-]{8,}\s[\d:]{3,}\s{2,}(.*)$' },        # Testcase
              }

# Parser setup
parser = argparse.ArgumentParser(description='Using a known set of archive formats, process a list of archives, unarchive, and remove original.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-c', dest='max_count', default=2, help='Only unarchive archives with this number of items or less.') 
parser.add_argument('-k', dest='keep', action='store_true', default=False, help='Do not remove the archive when done.')
# Maybe add an alternate extract location?
# Maybe add recursion -- but this is hard since we can also process directories, so we would have to clean up overlaps
#parser.add_argument('-R', dest='recurse', action='store_true', default=False, help='Recurse into directories.')
parser.add_argument('-t', dest='test', action='store_true', default=False, help='Do all actions except unarchive and delete..')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('-ntrash', dest='trash', action='store_const', const=None, default='__Trash',  help='Disable use of Trash folder.')
parser.add_argument('items', nargs=argparse.REMAINDER)

# True out arg parser
args = parser.parse_args()

# Patch verbose levels
if args.debug:
  args.verbose = True

# Check for at least one item 
if len(args.items) < 1:
  print("ERROR: At least one archive or diretory is required")
  sys.exit(1)

# Check the binaries and make sure they are on the system
# TODO: Try to which these to get ehm dynamically
inigo = False
for unarchiver in unarchivers.keys():
  if os.path.isfile(unarchivers[unarchiver]['binary']) and os.access(unarchivers[unarchiver]['binary'], os.X_OK):
    if args.debug:
      print("Unarchiver", unarchiver, "found:", unarchivers[unarchiver]['binary'])
  else:
    inigo = True
    print("ERROR: Unarchiver", unarchiver, "not found:", unarchivers[unarchiver]['binary'])
if inigo:
  sys.exit(1)
      
# Build a source list of potential archives
for item in args.items:
  if os.path.isfile(item):
    sourcelist.append(os.path.abspath(item))
  elif os.path.isdir(item):
    for file_item in os.listdir(item):
      if os.path.isfile(os.path.join(item, file_item)):
        sourcelist.append(os.path.abspath(os.path.join(item, file_item)))
if args.debug:
  print("sourcelist:", sourcelist)

# Iterate through the list
for sourcefile in sourcelist:
  root = None
  root_multipart = None
  ext = None
  multipart = False
  multipart_base = False

# Check to see if the file is an archive
  (root, ext) = os.path.splitext(sourcefile)
  if ext:
    ext = ext.lstrip('.')
    ext = ext.lower()
    if ext not in unarchivers:
      if args.debug:
        print("INFO: Skipping file", sourcefile, "since doesn't have an unarchivable extension")
      continue 
  else:
    if args.verbose:
      print("INFO: Skipping file ", sourcefile, "as it doesn't have an extension")
    continue

  if args.verbose:
    print('Inspecting file', sourcefile)

# Check to see if the file is part of multipart archive (and if so, process only the root)
#  print(ext)
#  print(octal_dump(ext))
#  print(unarchivers[ext])
#  if ext in unarchivers:
#    print("Got here") 
#  print(sourcefile, ext)
  if 'multipart_string' in unarchivers[ext]:
    for multipart_string_spec in unarchivers[ext]['multipart_string']:
      fname_multipart = re.search(multipart_string_spec, sourcefile, re.IGNORECASE)
      if fname_multipart:
        multipart = True
        for multipart_basespec in unarchivers[ext]['multipart_base']:
          fname_multipart_base = re.search(multipart_basespec, sourcefile, re.IGNORECASE) 
          if fname_multipart_base:
            multipart_base = True
  if multipart:
    if not multipart_base:
      if args.verbose:
        print("INFO: Skipping file ", sourcefile, "as it a segment of a multipart archive")
      continue
    else:
      if args.verbose:
        print("INFO: File ", sourcefile, "is the base of a muultipart archive")

# Find a new file root for multipart comparison
  if multipart:
    if 'multipart_string' in unarchivers[ext]:
      for multipart_string_spec in unarchivers[ext]['multipart_string']:
        fname_multipart = re.search(multipart_string_spec, sourcefile, re.IGNORECASE)
        if fname_multipart:
          root_multipart = re.sub(multipart_string_spec, "", sourcefile)

# Get items in archive 
  objects = get_objects_in_archive(archive=sourcefile, unarchiver_spec=unarchivers[ext], debug=args.debug)
  if args.debug:
    print(objects)

  if args.verbose:
    print(len(objects),"items")

  if len(objects) <= int(args.max_count):
# Make sure none of the archive files exist
    found_objects = False
    for object in objects:
      if os.path.exists(object):
        found_objects = True
        if True:
          print("WARNING:Skipping", sourcefile, "since", object, "was found on the filesystem.")
    if found_objects:
      print("WARNING:Skipping", sourcefile, "since an object from the archive was already found on the filesystem.")
      continue

# Extract the archive
    if args.test:
      print("TEST: Extract with command ", unarchivers[ext]['binary'], " ", unarchivers[ext]['extract_args'], " ", sourcefile)
    else:
      if 'extract_args' in unarchivers[ext]:
        if unarchivers[ext]['extract_args']:
          try:
            result = subprocess.run([unarchivers[ext]['binary'], unarchivers[ext]['extract_args'], sourcefile], timeout=1200, text=True, input='\n\n\n', stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
          except Exception as e:
            print("Error: Skipping", sourcefile, "as an extraction error occurred:", e)
            continue
      else:
        try:
          result = subprocess.run([unarchivers[ext]['binary'], sourcefile], timeout=1200, text=True, input='\n\n\n', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
          print("Error: Skipping", sourcefile, "as an extraction error occurred:", e)
          continue
      if args.debug:
        print("Command output:", result.stdout)
# Check the status code
# If it fails, then remove the partially extracted files
      if result.returncode != 0:
        print("WARNING: Command", unarchivers[ext]['binary'], unarchivers[ext]['extract_args'], sourcefile, "failed. Skipping remaining steps.")
        for object in objects:
          try:
            if args.trash:
              delete_file(os.path.abspath(object), args.trash)
              if args.debug:
                print("DEBUG: File", object, "removed due to failed extract of", sourcefile, "using local trash", args.trash)
            else:
              os.remove(os.path.abspath(object))
              if args.debug:
                print("DEBUG: File", object, "removed due to failed extract of", sourcefile, "directly")
          except:
            None  # File may not have been created
        continue
      else:
# It was ok, remove all parts of a multipart archive
        if multipart:
          for sourcefile in sourcelist:
            if root_multipart in sourcefile:
              if 'multipart_string' in unarchivers[ext]:
                for multipart_string_spec in unarchivers[ext]['multipart_string']:
                  fname_multipart_test = re.search(multipart_string_spec, sourcefile, re.IGNORECASE)
                  if fname_multipart_test:
                    try:
                      if args.trash:
                        delete_file(os.path.abspath(sourcefile), args.trash)
                        if args.debug:
                          print("DEBUG: File", sourcefile, "removed due after succesful multipart extract using local trash", args.trash)
                      else:
                        os.remove(os.path.abspath(sourcefile))
                        if args.debug:
                          print("DEBUG: File", source, "removed due after successful multipart extract of", sourcefile, "directly")
                    except:
                        print("Warning: Could not remove multipart source file %s." % sourcefile)            
# It was ok so remove the archive
        else:          
          try:
            if args.trash:
              delete_file(os.path.abspath(sourcefile), args.trash)
              if args.debug:
                print("DEBUG: File", sourcefile, "removed due after successful extract using local trash", args.trash)
            else:
              os.remove(os.path.abspath(sourcefile))
              if args.debug:
                print("DEBUG: File", source, "removed due after successfulmultipart extract of", sourcefile, "directly")
          except:
              print("Warning: Could not remove multipart source file %s." % sourcefile)
  else:
    if args.verbose:
      print("INFO: Skipping file", sourcefile, "as the current item count", str(len(objects)), "is greater than max_count", str(args.max_count))

print("DONE.")

