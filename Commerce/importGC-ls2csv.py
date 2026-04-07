#!/usr/local/opt/python@3.7/bin/python3

# This tool imports the output of a list of DVD directories with a naming scheme like:
# <Studio>-<Title>[-<Title2>...][-Bad,Disc1,Disc2,SideA,SideB...]-Rating+GoodSceneCount][Rating2+GoodSceneCount2...]
# where all strings are Camelcase.
# -Bad,-BAD can be processed but likely won't be in GC Star to update
# Mulitple Sides or Discs should the combined into a sigle rating [0..10] where 8: Excellent, 1: Failure/Discard, 6: Average (where most scenes are decent)

# Possible internal structure:
#{ normalized_studio: { normalized_title: [ { sub_title: W, original_title: X, original_studio: Y, original_rating: float(1-10), bad: bool, side: chr(1), disc_num: chr(1) }, ... ], normalized_rating: int(1-10),
#                       normalized_title: [ { sub_title: A, original_title: B, original_studio: C, original_rating: float(1-10), bad: bool, side: chr(1), disc_num: chr(1) }, ... ], normalized_rating: int(1-10),
#                       ... },
#  normalized_studio: ... }  

#sudo pip-3.6 install fuzzywuzzy

import argparse
import copy
import csv
import fuzzywuzzy
import logging
#import os
import pprint
import re
import sys
#import time
from fuzzywuzzy import fuzz
#import glob
#from chardet.universaldetector import UniversalDetector

# Get out of nested loops
class nested_beakout(Exception): pass

def get_title_field(csvobj):
  columnNames= [ 'Title', 'Name' ]
  extractedNames = []
# For Reader
#  for column in csvobj.next():
#    extractedNames.append(column)
# For DictReader
  extractedNames = csvobj.fieldnames
#  pprint.pprint(extractedNames)
  for possibleName in columnNames:
    if possibleName in extractedNames:
      return possibleName
  return None

def get_studio_field(csvobj):
  columnNames= [ 'Studio' ]
  extractedNames = []
# For Reader
#  for column in csvobj.next():
#    extractedNames.append(column)
# For DictReader
  extractedNames = csvobj.fieldnames
#  pprint.pprint(extractedNames)
  for possibleName in columnNames:
    if possibleName in extractedNames:
      return possibleName
  return None

def get_trailing_number(s):
  m = re.search(r'\d+$', s)
  if m:
    return int(m.group())
  else: None

def remove_trailing_paren(s):
  m = re.sub(r'\s+\(.*\)$','',s)
  return m 

def decamel(s):
  last_char = len(s) - 1
#  print(last_char)
  if last_char < 1:
    return None
  elif last_char == 1 or last_char == 2:
    return s
  else:
    char_index = 1
    temp_buffer = s[0]
    while char_index < last_char:
#      print(temp_buffer)
#      print(char_index)
      if s[char_index].isupper():
        if s[char_index+1].islower() and s[char_index-1].isalpha():
#          print("In upper-lower")
          temp_buffer = temp_buffer + ' ' + s[char_index]
        else:
          temp_buffer = temp_buffer + s[char_index]
      elif s[char_index].isdigit():
        if s[char_index+1].isalpha():
#          print("In digit-alpha")
          temp_buffer = temp_buffer + s[char_index] + ' '
        else:
          temp_buffer = temp_buffer + s[char_index]
      else:
        temp_buffer = temp_buffer + s[char_index]
      char_index = char_index + 1
    temp_buffer = temp_buffer + s[char_index]
#    print(temp_buffer)
    return temp_buffer

#def get_encoding(filename):
#  detector = UniversalDetector()
#  detector.reset()
#  for line in open(filename, 'rb'):
#    detector.feed(line)
#    if detector.done: break
#  detector.close()
#  if detector.result['encoding']:
#    temp_encoding = detector.result['encoding'].lower()
#    if "utf" in temp_encoding:
#      temp_encoding = temp_encoding.replace("-", "_")
#    return temp_encoding
#  else:
#    return None

# Global Variables
#passingScore = 83 
studios = []

# Parser setup
parser = argparse.ArgumentParser(description='Take a list of movies w/ ratings (previous list of directories in a set format and listed with ls -1), and map those ratings back to a GCS library file.')
parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-u', dest='update', action='store_true', default=False,  help='Enable writing to the CSStar file.')
parser.add_argument('-g', dest='gcslibrary',  help='GC Star library file to write to.')        
parser.add_argument('-s', dest='studiolist', default='./advdmstudio.csv', help='A list of studios to match against ls -1 file.') 
parser.add_argument('-f', dest='titleslist', required=True, help='A list of titles in a ls -1 file.')

# Patterns
re_studio = re.compile('^([^\-]*)', flags=re.IGNORECASE)
re_rating = re.compile('\-*(\d.\d+)\-*', flags=re.IGNORECASE)
re_title = re.compile('\^[^\-]*-([^\-]*)\-*', flags=re.IGNORECASE)
# Wait on these. If we see these in the title maches it would be easier to filter them out in normal sub-title scanning
re_bad = re.compile('(-Bad.*)[$,\-]', flags=re.IGNORECASE)
#re_side =
#re_disc =

# True out arg parser
args = parser.parse_args()

# Set up the logger
if args.debug:
  logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
else:
  logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
log = logging.getLogger(__name__)
##for lh in ("pynoc", "pynoc.apc", "paramiko", "paramiko.transport"):
##    logging.getLogger(lh).setLevel(100)

# Read in the studio file
log.debug("Opening studio file %s", args.studiolist)
try:
  studios_raw = open(args.studiolist, 'r', encoding='utf-8-sig')
#  studios_raw = open(args.studiolist 'rt', encoding=get_encoding(args.studiolist))
  for buf in csv.DictReader(studios_raw):
    studios.append(copy.deepcopy(buf))
except Exception as e:
  print(e)
  sys.exit(1)

#pprint.pprint((studios))

# If in update mode
if args.update:
  None
## Confirm that the GCStar library can be found
## Confirm that CGStar is not running

# Read ls -1 file
log.debug("Opening ls -1 file %s", args.titleslist)
try:
  titles = open(args.titleslist, 'r', encoding='utf-8-sig')
#  titles = open(args.titleslist 'rt', encoding=get_encoding(args.titleslist))
except Exception as e:
  print(e)
  sys.exit(1)

# Bucket for results
normalized_results = {}

# For each title
for title in titles:
  normalized_studio = None
  bad_flag = False
  # Extra newline filtering
  title = title.strip()
  if title:
    # Make sure that that there is one or more rating
    rating_matches = re.findall(re_rating, title)
    if len(rating_matches) < 1:
      log.warning("Skipping title %s as no valid rating string could be found." % title)
      continue
    # Process the studio
    studio_matches = re.findall(re_studio, title)
    if len(studio_matches) != 1:
      log.warning("Skipping title %s as no valid studio string could be found." % title)
      continue
    camel_studios = studio_matches[0]
    # Handle studio and sub-studio cases, ex: studio(sub-studio) -> PurePlay(Sweethearts), where we try to match the sub-studio first
    camel_studios = camel_studios.replace(')', '')
    camel_studios = camel_studios.split('(')
    log.debug("camel_studios: %s" % camel_studios)
    try:
      for camel_studio in reversed(camel_studios):
        string_studio = decamel(camel_studio)
        log.debug("string_studio: %s" % string_studio)
        ## Validate studio against map
        for studio_line in studios:
          if string_studio in studio_line['Studio']:
            log.debug("studio_line: %s" % studio_line)
            if 'Yes' in studio_line['Alias']:
              normalized_studio = studio_line['Origin']
              raise nested_beakout()
            else:
              normalized_studio = studio_line['Studio']
              raise nested_beakout()
    except nested_beakout:
      pass

    if normalized_studio is not None:
      log.debug("Found normilized_studio %s for %s" % (normalized_studio, title))
      if normalized_studio not in normalized_results.keys():
        normalized_results[normalized_studio] = {}
    else:
      log.warning("Skipping title %s as no normalized studio could be found." % title)
      continue
    
    ## Remove "BADs" and set flag
    bad_matches = re.findall(re_bad, title)
    if len(bad_matches) > 0:
      bad_flag=True
      title = re.sub(re_bad, '', title)
      log.debug("Bad filtered line now: %s" % title)
      

## Remove "Side" and set flag
## Remove "Disc" and set flag
## Split by Studio, then Title(s), then Ratings(s)
## UnCamel Title(s)
## Merge sides / titles into single entry
## Apply hysteresis on rating
## Confirm we can match title
## Buffer
# If "go"
## Make sure GCStar is not runing
## Take backup of current library file
## Load current library file
## For each item in Buffer
### Alter entry in library file
## Close library file

## For each title in master
#for masterRow in master:
#  # Filter title for studio
#  title = None
#  studio = None
#  values = masterRow[masterField].split(' - ')
#  if len(values) > 1:
#    title = values[0]
#    studio = values[1]
#  else:
#    title = values[0]
#  # Remove trailing parens
#  title = remove_trailing_paren(title)
#  # Set displayed flag to False
#  displayedOnce = False 
#
## Well this is lame, we can't reset the iterator on the DictReader. So we have to close the old one and open a new one each time.
#  # Read in the slave file
#  log.debug("Opening slave file %s", args.slavefile)
#  slave=None
#  slaveField=None
#  try:
#    fromSlave = open(args.slavefile, 'r', encoding='utf-8-sig')
##    fromSlave = open(args.slavefile, 'rt', encoding=get_encoding(args.slavefile))
#    slave = csv.DictReader(fromSlave)
#    slaveField = get_title_field(slave)
#    log.debug("Slave field is: %s", slaveField)
#  except Exception as e:
#    print(e)
### For each slavetitle in slave
#  for slaveRow in slave:
#    slaveTitle = None
#    slaveStudio = None
#    # Eek, can't assume this. Need to look for Studio? column in CSV
#    if get_studio_field(slave):
#      slaveTitle = slaveRow[slaveField]
#      slaveStudio = slaveRow[get_studio_field(slave)]
#    else:
#      values = slaveRow[slaveField].split(' - ')
#      if len(values) > 1:
#        slaveTitle = values[0]
#        slaveStudio = values[1]
#    # Remove trailing parens
#    slaveTitle = remove_trailing_paren(slaveTitle)
#### Get score
#    ratio = fuzz.ratio(title, slaveTitle)
#### If number in a series don't match, then reduce the score?
#    masterNumber = get_trailing_number(title)
#    slaveNumber = get_trailing_number(slaveTitle)
#    if (masterNumber and slaveNumber):
#      if (masterNumber != slaveNumber):
#        # Part of a series and should never match
#        ratio = ratio - 18 
#    elif (masterNumber or slaveNumber):
#        # Part of a series, but one doesn't have a series number (like #1)
#        ratio = ratio - 20
#### If score is > X then print the source title and line number with all the matching slave titles and their line numbers
#    if ratio >= passingScore:
#      if not displayedOnce:
#        print("Master Title \tline %s:\t%s (%s)" % (str(master.line_num), title, studio))
#        displayedOnce=True
#      print(" Slv Ratio %s \tline %s:\t%s (%s)" % (ratio, str(slave.line_num), slaveTitle, slaveStudio))
#  fromSlave.close()
