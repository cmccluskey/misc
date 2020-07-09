#!/usr/bin/python3

import argparse
import errno
import hashlib
import logging
import os
import pprint
import re
import shutil 
import sys


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
parser.add_argument('-ntrash', dest='trash', action='store_const', const=None, default='.Trash',  help='Disable use of Trash folder.')
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
if args.actionlog:
  try:
    af = open(args.actionlog, 'a')
  except IOError as e:
    logger.error("Cannot open action file %s for writing" % args.actionlog)
    os.exit(1)


files = build_file_tree(args.items, args.recurse)



#TODO
#Add aggressive checking of serial items
#Use Trash folder 
#Add trial mode to preview destructive changes
#Use a form loop pattern to allow for multiple pattern matches
#Pick a serial pattern for non-duplicate files what would hash to an exising name

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
#   A. Space at the end of the filename             #
#   B. Space at the end of the suffix               #
#   C. Double dots                                  #

# RE Filters
re_bad = re.compile('\`|\~|\@|\&|\;|\%|\!')
re_startcopyof = re.compile('^Copy\s*of\s*', re.IGNORECASE)
re_startplus = re.compile('^\++')
re_endcopy = re.compile('\s*copy$', re.IGNORECASE)
re_endcopyx
re_endcopynum
re_endplus = re.compile('\+*$')
re_startcopyparen
re_startcopyparenof
re_Id
re_enddashparens
re_endparens


checksum_cache = {}

for item in files:
#  print(item)
  original = item
  filename = None
  suffix = None
  (filename, suffix) = os.path.splitext(os.path.basename(item))
  basedir = os.path.dirname(item)
  checksum_cache[original] = cksum(original)
  if args.debug:
    logger.debug("Original: %s" % original)
    logger.debug("Original Sum: %s" % checksum_cache[original])
    logger.debug("Original File: %s" % filename )
    logger.debug("Original Suffix: %s" % suffix)
    logger.debug("Original Base Dir: %s" % basedir)

  if args.unixoffend:
    re_bad.sub('', filename)
    logger.debug("New File: %s" % filename)
    re_bad.sub('', suffix)
    logger.debug("New Suffix: %s" % suffix)

  re_startcopyof.sub('', filename)
  logger.debug("New File: %s" % filename)

  re_startplus.sub('', filename)
  logger.debug("New File: %s" % filename)

  re_endcopy.sub('', filename)
  logger.debug("New File: %s" % filename)

  re_endplus.sub('', filename)
  logger.debug("New File: %s" % filename)

  re_endplus.sub('', suffix)
  logger.debug("New Suffix: %s" % suffix)

#
#  # .Id_NN 
#  re_Id = re.compile(r'\.Id_[0-9]+\.')
#  done = False
#  while not done and not deleted:
#    if re_Id.search(item):
##      print("Here")
#      if args.debug:
#        print("In: re_Id")
#      itemtest = re_Id.sub('.', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_Id")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if args.debug:
#          print("New Item: %s" % itemtest )
#          print("New Item: %s" % item_sum )
#        if original_sum == item_sum:
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue 
#    else:
#      done = True
#
#  # 'Copy of '
#  re_CopyOf = re.compile(r'^Copy\sof\s', flags=re.IGNORECASE)
#  done = False
#  while not done and not deleted:
#    if re_CopyOf.match(item):
#      if args.debug:
#        print("In: re_CopyOf")
#      itemtest = re_CopyOf.sub('', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_CopyOf")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if original_sum == item_sum:
#          if args.debug:
#            print("New Item: %s" % itemtest )
#            print("New Item: %s" % item_sum )
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue
#    else:
#      done = True  
#
## 'Copy (NN) of '
#  re_CopyOfParen = re.compile(r'^Copy\s\([0-9]+\)of\s', flags=re.IGNORECASE)
#  done = False
#  while not done and not deleted:
#    if re_CopyOfParen.match(item):
#      if args.debug:
#        print("In: re_CopyOfParen")
#      itemtest = re_CopyOfParen.sub('', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_CopyOfParen")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if original_sum == item_sum:
#          if args.debug:
#            print("New Item: %s" % itemtest )
#            print("New Item: %s" % item_sum )
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue
#    else:
#      done = True
#
## ' copy' 
#  re_CopyEnd = re.compile(r'\scopy\.', flags=re.IGNORECASE)
#  done = False
#  while not done and not deleted:
#    if re.match(r'\.Id_[0-9]+\.', item):
#      if args.debug:
#        print("In: re_CopyEnd")
#      itemtest = re_CopyEnd.sub('.', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_CopyEnd")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if original_sum == item_sum:
#          if args.debug:
#            print("New Item: %s" % itemtest )
#            print("New Item: %s" % item_sum )
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue
#    else:
#      done = True
#
## ' copy N'
#  re_CopyEndCount = re.compile(r'\scopy\s[0-9]+\.', flags=re.IGNORECASE)
#  done = False
#  while not done and not deleted:
#    if re_CopyEndCount.match(item):
#      if args.debug:
#        print("In: re_CopyEndCount")
#      itemtest = re_CopyEndCount.sub('.', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_CopyEndCount")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if original_sum == item_sum:
#          if args.debug:
#            print("New Item: %s" % itemtest )
#            print("New Item: %s" % item_sum )
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue
#    else:
#      done = True
#
## -(NNNNN)
#  re_EndCountDashParen = re.compile(r'\-\([0-9]+\)\.', flags=re.IGNORECASE)
#  done = False
#  while not done and not deleted:
#    if re_EndCountDashParen.match(item):
#      if args.debug:
#        print("In: re_EndCountDashParen")
#      itemtest = re_EndCountDashParen.sub('.', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_EndCountDashParen")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if original_sum == item_sum:
#          if args.debug:
#            print("New Item: %s" % itemtest )
#            print("New Item: %s" % item_sum )
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue
#    else:
#      done = True
#
## ' (NN)' or (NN)
#  re_EndCountParen = re.compile(r'\s?\([0-9]+\)\.', flags=re.IGNORECASE)
#  done = False
#  while not done and not deleted:
#    if re_EndCountParen.match(item):
#      if args.debug:
#        print("In: re_EndCountParen")
#      itemtest = re_EndCountParen.sub('.', item)
#      if original == itemtest:
#        print("Warning: Regex failed in re_EndCountParen")
#        done = True
#      else:
#        item_sum = cksum(itemtest)
#        if original_sum == item_sum:
#          if args.debug:
#            print("New Item: %s" % itemtest )
#            print("New Item: %s" % item_sum )
#          print("Will remove %s" % original)
#          os.remove(original)
#          done = True
#          deleted = True
#        else:
#          item = itemtest
#          continue
#    else:
#      done = True
#
