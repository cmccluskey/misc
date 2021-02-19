#!/opt/local/bin/python3

#sudo pip-3.6 install fuzzywuzzy

import argparse
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
from chardet.universaldetector import UniversalDetector

def get_encoding(filename):
  detector = UniversalDetector()
  detector.reset()
  for line in open(filename, 'rb'):
    detector.feed(line)
    if detector.done: break
  detector.close()
  if detector.result['encoding']:
    temp_encoding = detector.result['encoding'].lower()
    if "utf" in temp_encoding:
      temp_encoding = temp_encoding.replace("-", "_")
    return temp_encoding
  else:
    return None

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

def get_trailing_number(s):
  m = re.search(r'\d+$', s)
  if m:
    return int(m.group())
  else: None

def remove_trailing_paren(s):
  m = re.sub(r'\s+\(.*\)$','',s)
  return m 

# Variables
passingScore = 83 

# Parser setup
parser = argparse.ArgumentParser(description='Compare titles between two lists using a fuzzy search, and report outputs.')
parser.add_argument('-d',  dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-mf', dest='masterfile', default='./vids.csv', required=True, help='File to compare data from (source).') 
parser.add_argument('-sf', dest='slavefile', default=False, required=True, help='File to compare data of (discard).')

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

# Read in the master file
log.debug("Opening master file %s", args.masterfile)
master=None
masterField=None
try:
  fromMaster = open(args.masterfile, 'r', encoding='utf-8-sig')
#  fromMaster = open(args.masterfile, 'rt', encoding=get_encoding(args.masterfile))
  master = csv.DictReader(fromMaster)
  masterField = get_title_field(master)
  log.debug("Master field is: %s", masterField)
except Exception as e:
  print(e)

#pprint.pprint((master))
# For each title in master
for masterRow in master:
  # Filter title for studio
  title = None
  studio = None
  values = masterRow[masterField].split(' - ')
  if len(values) > 1:
    title = values[0]
    studio = values[1]
  else:
    title = values[0]
  # Remove trailing parens
  title = remove_trailing_paren(title)
  # Set displayed flag to False
  displayedOnce = False 

# Well this is lame, we can't reset the iterator on the DictReader. So we have to close the old one and open a new one each time.
  # Read in the slave file
  log.debug("Opening slave file %s", args.slavefile)
  slave=None
  slaveField=None
  try:
    fromSlave = open(args.slavefile, 'r', encoding='utf-8-sig')
#    fromSlave = open(args.slavefile, 'rt', encoding=get_encoding(args.slavefile))
    slave = csv.DictReader(fromSlave)
    slaveField = get_title_field(slave)
    log.debug("Slave field is: %s", slaveField)
  except Exception as e:
    print(e)
## For each slavetitle in slave
  for slaveRow in slave:
    slaveTitle = None
    slaveStudio = None
    # Eek, can't assume this. Need to look for Studio? column in CSV
    if ' - ' in slaveRow[slaveField]:
      values = slaveRow[slaveField].split(' - ')
      if len(values) > 1:
        slaveTitle = values[0]
        slaveStudio = values[1]
    else:
      slaveTitle = slaveRow[slaveField]
    # Remove trailing parens
    slaveTitle = remove_trailing_paren(slaveTitle)
### Get score
    ratio = fuzz.ratio(title, slaveTitle)
### If number in a series don't match, then reduce the score?
    masterNumber = get_trailing_number(title)
    slaveNumber = get_trailing_number(slaveTitle)
    if (masterNumber and slaveNumber):
      if (masterNumber != slaveNumber):
        # Part of a series and should never match
        ratio = ratio - 18 
    elif (masterNumber or slaveNumber):
        # Part of a series, but one doesn't have a series number (like #1)
        ratio = ratio - 20
### If score is > X then print the source title and line number with all the matching slave titles and their line numbers
    if ratio >= passingScore:
      if not displayedOnce:
        print("Master Title \tline %s:\t%s (%s)" % (str(master.line_num), title, studio))
        displayedOnce=True
      print(" Slv Ratio %s \tline %s:\t%s (%s)" % (ratio, str(slave.line_num), slaveTitle, slaveStudio))
  fromSlave.close()
