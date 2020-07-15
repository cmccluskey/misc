#!/usr/bin/python3

# 1. Do removal filters                             # 
#   A. Filename or suffix contains:                 #
#     Unix offending character sets [`,@,&,;,%,!,]  #
#   B. Filename starts with:                        #
#     'Copy of '                                    #
#     '+'                                           #
#   C. Filename Ends with:                          #
#     ' copy'                                       #
#     '+'                                           #
#   D. Suffix Ends with:                            #
#     '+'                                           #
#   E. Filename starts with:                        #
#     'Copy (NN) of '                               #
#     'Copy (NN)'                                   #
#   F. Filename contains:                           #
#     '.Id_NN'                                      #
#   G. Ends with on the filename:                   #
#     ' copy N'                                     #
#     '-(NNNNN)'                                    #
#     ' (NN)'                                       #
#     '(NN)'                                        #
#     'copy[0-9,a-z,A-Z]'                           #
#     'copyNN'                                      #
#   H. Suffix contains:                             #
#     '.Id_NN'                                      #
# 2. Do sequential checks                           #
#   A. '-(NNNN)'                                    #
# 3. Postfixes                                      #
#   A. Space at the beginning / end of the filename #
#   B. Space at the beginning / end of the suffix   #
#   C. Double dots                                  #


import argparse
import hashlib
import logging
import os
import re
import shutil 
import sys
import time
from fuzzywuzzy import fuzz


# Move to commmon
def build_file_tree(items=[], recurse=False):
  temp_dict = {}
  for item in args.items:
    if os.path.isfile(item):
      temp_dict[os.path.abspath(item)] = item 
    if item == '*':
      item = os.getcwd()
    if os.path.isdir(item):
      if recurse:
        for root, dirs, files in os.walk(item):
          for f in files:
            temp_dict[os.path.abspath(os.path.join(root,f))] = item
      else:
        for possiblefile in os.listdir(item):
          if os.path.isfile(os.path.join(item, possiblefile)):
            temp_dict[os.path.abspath(os.path.join(item, possiblefile))] = item
  return sorted(temp_dict.keys())


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
        os.mkdirs(trash_folder_pathed, exist_ok=True)
      except:
        logger.error("Cannot create trash folder %s" % trash_folder_pathed)
        sys.exit(1)
      # Action statement
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
    actionfile.write("\n")
    actionfile.write("Date: %s\n" % str(time.time()) )
    actionfile.write("Action: DeleteFile\n")
    actionfile.write("Object: %s\n" % filename)
       

def move_file(fromfile, tofile, actionfile):
  if os.path.isfile(tofile):
    logger.error("Move of %s would overwrite exsiting file %s." % (fromfile, tofile))
    sys.exit(1)
  else:
    try:
      shutil.move(fromfile,tofile)
    except:
      logger.error("Cannot move file %s to file %s" % (fromfile, tofile)) 
      sys.exit(1)
    actionfile.write("\n")
    actionfile.write("Date: %s\n" % str(time.time()) )
    actionfile.write("Action: MoveFile\n")
    actionfile.write("Object: %s\n" % fromfile)
    actionfile.write("Destination: %s\n" % tofile)


# Local
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
seriallength = 4


# Parser setup
parser = argparse.ArgumentParser(description='Looks for various files from copy processes and remove/rewrite the filename based on the results.')
parser.add_argument('-a', dest='aggressive', action='store_true', default=False, help='For items that can have an incremented value, search for duplicates before move/delete.')
parser.add_argument('-noffend', dest='unixoffend', action='store_false', default=True, help='Remove typically offending Unix shell characters.')
parser.add_argument('-R', dest='recurse', action='store_true', default=False, help='Recurse into directories.')
parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-r', dest='report', action='store_true', default=False, help='Report only, do not touch files.')
parser.add_argument('-nlog', dest='actionlog', action='store_const', const=None, default='action.log', help='Disable action log generation.')
parser.add_argument('-ntrash', dest='trash', action='store_const', const=None, default='__Trash',  help='Disable use of Trash folder.')
parser.add_argument('items', nargs='+', default=None)
args = parser.parse_args()


# Enable logger
logging.basicConfig()
logger = logging.getLogger(__name__)
if (args.debug):
   logger.setLevel(logging.DEBUG)
else:
   logger.setLevel(logging.ERROR)
#for lh in (""):
#   logging.getLogger(lh).setLevel(100)


# Test write of actionlog
af = None
if args.actionlog:
  try:
    af = open(args.actionlog, 'a')
  except IOError as e:
    logger.error("Cannot open action file %s for writing" % args.actionlog)
    os.exit(1)


files = build_file_tree(args.items, args.recurse)

# RE Filters
re_bad = re.compile('\`|\~|\@|\&|\;|\%|\!')
re_startcopyof = re.compile('^Copy\s?of\s?', re.IGNORECASE)
re_startplus = re.compile('^\++')
re_startcopyparen = re.compile('^Copy\s?\(\d+\)\s?', re.IGNORECASE)
re_startcopyparenof = re.compile('^Copy\s?\(\d+\)\s?of\s?', re.IGNORECASE)
re_startdollar = re.compile('^\$+')
re_endcopy = re.compile('\s*copy$', re.IGNORECASE)
re_endcopyx = re.compile('\s*copy\s?\w{1,2}$', re.IGNORECASE)
re_endcopynum = re.compile('\s*copy\s?\d?$', re.IGNORECASE)
re_endplus = re.compile('\+*$')
re_endparens = re.compile('\s?\(\d+\)$')
re_endbrackets = re.compile('\s?\[\d+\]$')
re_enddollar = re.compile('\$+$')
re_Id = re.compile('\.?Id_\d+$')

# Special use cases
re_enddashparens = re.compile('\s?-\(\d+\)$')
re_doubledot = re.compile('\.+')
re_startwithspace = re.compile('^\s+')
re_endswithspace = re.compile('\s+$')
re_startdot = re.compile('^\.{1,1}')

# Exclude cases for ++
re_containsc = re.compile('c\+\+', re.IGNORECASE)
re_containsg = re.compile('g\+\+', re.IGNORECASE)
re_containsmagick = re.compile('magick\+\+', re.IGNORECASE)
re_containsmotif = re.compile('motif\+\+', re.IGNORECASE)
re_containsbonnie = re.compile('bonnie\+\+', re.IGNORECASE)


checksum_cache = {}

for item in files:
  original = item
  filename = None
  suffix = None
  (filename, suffix) = os.path.splitext(os.path.basename(item))
  if suffix:
    suffix = re_startdot.sub('', suffix)
  originalsuffix = suffix
  basedir = os.path.dirname(item)
  checksum_cache[original] = cksum(original)
  if args.debug:
    logger.debug("Original: %s" % original)
    logger.debug("Original Sum: %s" % checksum_cache[original])
    logger.debug("Original File: %s" % filename )
    logger.debug("Original Suffix: %s" % suffix)
    logger.debug("Original Base Dir: %s" % basedir)

# 1A Remove Unix offending character sets
  if args.unixoffend:
    filename = re_bad.sub('', filename)
    logger.debug("New File: %s" % filename)
    suffix = re_bad.sub('', suffix)
    logger.debug("New Suffix: %s" % suffix)

# 1B Filename starts with
  filename = re_startplus.sub('', filename)
  logger.debug("New File: %s" % filename)

  filename = re_startdollar.sub('', filename)
  logger.debug("New File: %s" % filename)

  filename = re_startcopyof.sub('', filename)
  logger.debug("New File: %s" % filename)

# 1C Filename ends with
  if not (re_containsc.search(filename) or re_containsg.search(filename) or re_containsmagick.search(filename) or
          re_containsmotif.search(filename) or re_containsbonnie.search(filename)):
    filename = re_endplus.sub('', filename)
    logger.debug("New File: %s" % filename)

  filename = re_enddollar.sub('', filename)
  logger.debug("New File: %s" % filename)

  filename = re_endcopy.sub('', filename)
  logger.debug("New File: %s" % filename)

# 1D Suffix ends with
  suffix = re_endplus.sub('', suffix)
  logger.debug("New Suffix: %s" % suffix)

# 1E Filename starts with
  filename = re_startcopyparenof.sub('', filename)
  logger.debug("New File: %s" % filename)
  filename = re_startcopyparen.sub('', filename)
  logger.debug("New File: %s" % filename)

# 1F Filename contains
  filename = re_Id.sub('', filename)
  logger.debug("New File: %s" % filename)

# 1G Filename ends with
  filename = re_endcopynum.sub('', filename)
  logger.debug("New File: %s" % filename)
  filename = re_enddashparens.sub('', filename)
  logger.debug("New File: %s" % filename)
  filename = re_endparens.sub('', filename)
  logger.debug("New File: %s" % filename)
  filename = re_endbrackets.sub('', filename)
  logger.debug("New File: %s" % filename)
  filename = re_endcopyx.sub('', filename)
  logger.debug("New File: %s" % filename)

# 1H Suffix contains
  suffix = re_Id.sub('', suffix)
  logger.debug("New Suffix: %s" % suffix)

# 2A Do sequential checks
# Note: In theory we should have folded the file down to its concise, non-copied form. Check the filename against other files in the same directory. 
# And if the concise form matches another file, then run checksums on the other file. If it matches, then delete the version of the file that is
# farthest from the most concise form.
  # Get local files
  localfiles = build_file_tree(basedir)
  deleted = False
  if args.aggressive:
    for localfile in localfiles:
      (localfilename, localsuffix) = os.path.splitext(os.path.basename(localfile))
      # If the local file is a possible varaint of the copy-stripped file
      if filename in localfilename:
        # Make sure we haven't seen ourselves
        if not os.path.samefile(original, localfile):
          if not localfile in checksum_cache.keys():
            checksum_cache[localfile] = cksum(localfile)
          # Did we find something that needs to be deleted
          logger.debug("Localfile checksum: %s" % checksum_cache[localfile])
          logger.debug("Original checksum: %s" % checksum_cache[original])   
          if (checksum_cache[localfile] == checksum_cache[original]): # Same checksum so one has to go
            # Do a Levenshtein distance to the copy-stripped file. Closet file to the stripped version is the best.
            originalratio = int(fuzz.ratio(filename, original))
            localratio = int(fuzz.ratio(filename, localfilename))
            logger.debug("Localfile fuzzy ratio: %s" % str(localratio))
            logger.debug("Original fuzzy ratio: %s" % str(originalratio))
            if (originalratio > localratio):
              if args.report:
                print("Altername file %s will be deleted due to hashing match with %s (aggressive)" % (localfile, original))
              else:
                delete_file(localfile, args.trash, af)
                checksum_cache.pop(localfile)
            else:
              deleted = True
              if args.report:
                print("File %s will be deleted due to hashing match with %s (aggressive)" % (original, localfile))
              else:
                delete_file(originalfile, args.trash, af)
                checksum_cache.pop(original)

  if not deleted:
# 3 Postfixes -- not going to do any of these now, as I hope the logic above isn't so sloppy to need them
# 3A Space at the begin/end of the filename
#re_startwithspace = re.compile('^\s+')
#re_endswithspace = re.compile('\s+$')
# 3B Space at the begin/end of the suffix
#re_startwithspace = re.compile('^\s+')
#re_endswithspace = re.compile('\s+$')
# 3C Double dots 
#re_doubledot = re.compile('\.+')

# 4 Final move or reporting
    # Combine file to pull path
    if suffix:
      recombinedfile = filename + '.' + suffix
      newfile = os.path.join(basedir, recombinedfile)
    else:
      newfile = os.path.join(basedir, filename)
    # Find an avaialble, sequential slot (delete if necessary)
    if newfile == original:
      logger.debug("File %s remains untouched" % original)
    else:
      if not os.path.isfile(newfile):
        if args.report:
          print("File %s will be moved from %s" % (newfile, original))
        else:
          move_file(original, newname, af)
          checksum_cache[newname] = checksum_cache[original]
          checksum_cache.pop(original)
      else:
        # Before we loop finding a new postscript, make sure and existing file on disk isn't the same
        if os.path.samefile(original, newfile):
          logger.info("We shouldn't have got to this point in the final move, the original file shouldn't have gone into the loop branch")
          sys.exit(1)
        if not newfile in checksum_cache.keys():
          checksum_cache[newfile] = cksum(newfile)
        # Did we find something that needs to be deleted
        logger.debug("Newfile (existing) checksum: %s" % checksum_cache[newfile])
        logger.debug("Original checksum: %s" % checksum_cache[original])
        if (checksum_cache[newfile] == checksum_cache[original]): # Same checksum so one has to go
          if args.report:
            print("File %s will be deleted due to hash map match on another file %s" % (original, newfile))
          else:
            delete_file(original, args.trash, af)
            checksum_cache.pop(original)
        else:
          # Would like to make this modular for but now we will use -(NNNN) as the sequence
          for counter in range(10000):
            if counter == 9999:
              logger.info("Counter overflow. This shouldn't happen")
              sys.exit(1)
            postscript = '-(' + format(counter, '04') + ')'
            testfilename = filename + postscript
            if suffix:
              testrecombinedfile = testfilename + '.' + suffix
              newfile = os.path.join(basedir, testrecombinedfile)
              logger.debug("In counter loop with %s for %s" % (str(counter), newfile))
            else:
              newfile = os.path.join(basedir, testfilename)
              logger.debug("In counter loop with %s for %s" % (str(counter), newfile))
            if not os.path.isfile(newfile):
              if args.report:
                print("Intecremented file %s will be moved from %s" % (newfile, original))
              else:
                move_file(original, newname, af)
                checksum_cache[newname] = checksum_cache[original]
                checksum_cache.pop(original)
              break
            else:
              if os.path.samefile(original, newfile):
                logger.info("We shouldn't have got to this point in the final move, the original file shouldn't have gone into the loop")
                sys.exit(1)
              if not newfile in checksum_cache.keys():
                checksum_cache[newfile] = cksum(newfile)
              # Did we find something that needs to be deleted
              logger.debug("Newfile (existing) checksum: %s" % checksum_cache[newfile])
              logger.debug("Original checksum: %s" % checksum_cache[original])
              if (checksum_cache[newfile] == checksum_cache[original]): # Same checksum so one has to go
                if args.report:
                  print("File %s will be deleted due to hash map match on another file %s" % (original, newfile))
                else:
                  delete_file(original, args.trash, af)
                  checksum_cache.pop(original)

