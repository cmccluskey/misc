#!/usr/bin/python

import argparse
import logging
import os
import pprint
import re
import shutil
import sys

# TODO:
# 8. Check alternate directory case
# 20. Implement alpha hash

def get_args():
   parser = argparse.ArgumentParser()
   parser.add_argument('-c', '--copy', 
                       required=False, action='store_true', default=False,
                       help='Copy instead of move files')
   parser.add_argument('-a', '--altdir',
                       required=False, action='store', default=None,
                       help='Use this destination directory instead of hashing to the same directory as the file(s)')
   parser.add_argument('-f', '--force',
                       required=False, action='store_true', default=False,
                       help='Force overwrite of the destination')
   parser.add_argument('-m', '--method',
                       required=True, action='store', default='bignumber',
                       help='Hashing method (bignumber, alpha, sha (TBD))')
   parser.add_argument('-d', '--debug',
                       required=False, action='store_true', default=False,
                       help='Set verbose/debug mode')
   parser.add_argument('-t', '--testing',
                       required=False, action='store_true', default=False,
                       help='Do not do the operation, but just test it')
   parser.add_argument('-l', '--level',
                       required=True, action='store', default=None,
                       help='Hash to N levels of directories, default: hash to the entire value')
   parser.add_argument('-i', '--input',
                       required=True, action='store', nargs='+',
                       help='Directory, file, or list of files to hash')

   args = parser.parse_args()
   return args
 

def rchop(thestring, ending):
   logger.debug("thestring: -=%s=-", thestring)
   logger.debug("ending: -=%s=-", ending)
   if thestring.endswith(ending):
      return thestring[:-len(ending)]
   return thestring

def extract_max_number(thestring):
#   logger.debug("thestring: %s", thestring)
   numbers = re.findall('\d*', thestring)
   numbers = filter(lambda x: x != '', numbers)
   logger.debug("numbers: %s", numbers)
   if (len(numbers) > 0):
#      numbers = map((lambda x: int(x)), numbers)
      maxnumber = max(numbers, key=len)
      logger.debug("maxnumber: %s", maxnumber)
      return maxnumber
   else: 
      return None
   
def hash_bignumber(filename):
   hash_array=[]
   filename_short = os.path.basename(filename)
   logger.debug("filename_short: %s", filename_short)
   number = extract_max_number(filename_short)
   if (number):
     hash_array.append(filename_short)
     temp_path = '' 
     for hashitem in list(number):
        temp_path = temp_path + hashitem + '/'
        hash_array.append(temp_path + filename_short)
   else:
     # Won't work for non-Posix
     hash_array.append(filename_short)
     hash_array.append('_/' + filename_short)
   return hash_array

def hash_alpha(filename):
   hash_array=[]
   filename_short = os.path.basename(filename)
   logger.debug("filename_short: %s", filename_short)
   fixedstr = ''
   if (len(os.path.splitext(filename_short)) > 1):
      fixedstr = os.path.splitext(filename_short)[0]
   else:
      fixedstr = filename_short
   fixedstr = fixedstr.upper()
   fixedstr = re.sub('[^0-9a-zA-Z]','_',fixedstr)
   fixedstr = re.sub('[\x00-\x2F\x3A-\x40\x5B-\x60\x7B-\x7F]','_',fixedstr)
   temp_path = ''
   hash_array.append(filename_short)
   for hashitem in list(fixedstr):
      temp_path = temp_path + hashitem + '/'
      hash_array.append(temp_path + filename_short)
   return hash_array

# Process args
args = get_args()

# Setup logger
#if (args.debug):
#   logging.basicConfig(sys.stderr, level=logging.DEBUG)
#else:
#   logging.basicConfig(sys.sederr, level=logging.ERROR)
logging.basicConfig()
logger = logging.getLogger(__name__)
if (args.debug):
   logger.setLevel(logging.DEBUG)
else:
   logger.setLevel(logging.ERROR)
#for lh in (""):
#   logging.getLogger(lh).setLevel(100)

# See if we have been passed a directory
if (len(args.input) == 1 and os.path.isdir(args.input[0])):
   logger.debug("Activating directory read...")
   files = os.listdir(args.input[0]) 
#   files = map((lambda x: args.input[0] + '/' + x), files)
   os.chdir(args.input[0]) 
   logger.debug("files now has %s entries.", str(len(files)))
else:
   files = args.input

# Get file in list
for fileentry in files:
# Top scope (per loop variables)
   current_path = None
   current_file = None
   current_path_full= None
   dst_root = None
 
   logger.debug("fileentry: -=%s=-", fileentry)
# Is the arg entry a file?
   if not os.path.isfile(fileentry):
      logger.info("Skipping entry %s since it is not a file", fileentry)
   else:
      current_file_full = os.path.normpath(os.path.abspath(fileentry))
      logger.debug("current_file_full: %s", current_file_full)
## Define the file and root
      current_file = os.path.basename(current_file_full)
      current_path = os.path.dirname(current_file_full)
      if not current_path:
         current_path = os.getcwd()
## Get the hash
      if args.method == 'bignumber':
         entry_hash = hash_bignumber(current_file)
      elif args.method == 'alpha':
         entry_hash = hash_alpha(current_file)
#      elif args.method == 'sha':
#         entry_hash = hash_sha(current_file)
      else:
         logger.error("Don't know about hash method %s", args.method)
         sys.exit(1)
      logger.debug("Created hash %s", entry_hash)
## Define the destination
      if (args.altdir):
         proposed_destination = args.altdir
      else:
         proposed_destination = current_path
#      proposed_destination = dst_root + '/' + current_file
### See if we can unwind the hash structure to see if the file already exsits
### in a hashed foldr structure
      index_found = None
      items_in_hash = len(entry_hash)
      index = items_in_hash - 1
      proposed_destination_full = proposed_destination + '/' + current_file
      while (index >= 0):
         proposed_subpath = str(entry_hash[index])
         if proposed_subpath in proposed_destination_full:
            index_found = index
            logger.debug("Found match in hash at index %s", index)
            break
         index -= 1
   # This should always match on at least entry_hash[0]
      logger.debug("index_found: %s", index_found)
      if (index_found is None): 
         logger.debug("Couldn't find a proper index in the hash. Will use the default filename/path.")
         index_found = 0
#### If we can unwind to a known parent level, reset the destination directory to adjust
      else:
         logging.debug("proposed_destination before rchop: %s", proposed_destination)
         proposed_destination = rchop(proposed_destination_full, entry_hash[index_found])
         logging.debug("proposed_destination after rchop: %s", proposed_destination)

### Now apply the preferred index in the hash
      preferred_index = index_found
      if (index_found > len(entry_hash)):
         preferred_index = len(entry_hash) - 1
      else: 
         if (int(args.level) > (len(entry_hash) -1)):
	    preferred_index = (len(entry_hash) -1)
         else:
            preferred_index = int(args.level)
      proposed_destination = proposed_destination + '/' + entry_hash[preferred_index]
      proposed_destination = os.path.normpath(proposed_destination)
### If proposed_destination already exists
      logging.debug("Final current_file_full: %s", current_file_full)
      logging.debug("Final proposed_destination: %s", proposed_destination)
      if os.path.exists(proposed_destination):
#### If force
         if args.force:
            logger.debug("Forcing...")
##### If copy, then copy
            if args.copy:
               print("{0} >-> {1}".format(current_file_full, proposed_destination))
               if not args.testing:
                  try:
                     os.makedirs(os.path.dirname(proposed_destination) )
                  except Exception, e:
                     logging.debug("makedirs error: %s", e)
                  shutil.copy2(current_file_full, proposed_destination)
##### Else move
            else:
               print("{0} -->{1}".format(current_file_full, proposed_destination))
               if not args.testing:
                  try:
                     os.makedirs(os.path.dirname(proposed_destination))
                  except Exception, e:
                     logging.debug("makedirs error: %s", e)
                  shutil.move(current_file_full, proposed_destination)
#### Else throw warning
         else:
            logger.warning("Skipping operation to proposed_destination as it would overwrite a currnet file")
      else:
### Else 
##### If copy, then copy
         if args.copy:
            print("{0} >-> {1}".format(current_file_full, proposed_destination))
            if not args.testing:
               try:
                  os.makedirs(os.path.dirname(proposed_destination))
               except Exception, e:
                  logging.debug("makedirs error: %s", e)
               shutil.copy2(current_file_full, proposed_destination)
##### Else move
         else:
            print("{0} --> {1}".format(current_file_full, proposed_destination))
            if not args.testing:
               try:
                  os.makedirs(os.path.dirname(proposed_destination))
               except Exception, e:
                  logging.debug("makedirs error: %s", e)
               shutil.move(current_file_full, proposed_destination)

