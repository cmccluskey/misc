#!/usr/local/opt/python@3.7/bin/python3

import argparse
import copy
import csv
import logging
import os
import pprint
import re
import requests
import sys
import time
from bs4 import BeautifulSoup
from decimal import Decimal

# Parser setup
parser = argparse.ArgumentParser(description='Pull wish list from a known website, and export the wishlist to a CSV file.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-c', dest='csvfile', default='./advdmstudio.csv', help='Override the CSV file.') 
parser.add_argument('-u', dest='user', default=False, required=True, help='Website user.')
parser.add_argument('-p', dest='pswd', default=False, required=True, help='Website user\'s password.')
parser.add_argument('-S', dest='site', default=False, required=True, help='Website URL without the leading protocol and double slash.')
parser.add_argument('-r', dest='reset', default=False, required=False, help='Do not receive alerts for items below this threshold.')

# True out arg parser
args = parser.parse_args()
testing = False # Testing the reset functionality

# Set up the logger
if args.debug:
  logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
  log = logging.getLogger(__name__)
##for lh in ("pynoc", "pynoc.apc", "paramiko", "paramiko.transport"):
##    logging.getLogger(lh).setLevel(100)
else:
  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  log = logging.getLogger(__name__)

if os.path.exists(args.csvfile):
  os.remove(args.csvfile)
    
# Setup Requests Handle and Params
requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.5) Gecko/20041111 Firefox/1.0'})
session.headers.update({'Accept-Encoding': 'x-gzip'})
session.headers.update({'Accept': 'text/html, application/xml'})

login = 'https://' + args.site + '/xcart/adult_dvd/login.php'
try:
  resp = session.get(login)    # retrieve cookie, tokens, and other stuff
  if resp.status_code == 200:
    None
  else:
    log.error("Return Code %s" % str(resp.status_code))
except Exception as e:
  log.error("%s" % str(e))


values = { 'mode': 'login', 'adult_dvd_id': '', 'usertype': 'C', 'username': args.user, 'password': args.pswd, 'redirect': 'adult_dvd' }
try:
  resp = session.post(login, data=values)    # perform the login
  if resp.status_code == 200:
    None
  else:
    log.error("Return Code %s" % str(resp.status_code))
except Exception as e:
  log.error("%s" % str(e))

# What page we on now?
currentp = 1
# What is the number of pages to read
maxp = 26 
# Beautiful Soup buffers
soup = None
soupdata = None

if testing:
  listings = [] # Can be filled with a lists of data
else:
  listings = [['Origin', 'MapTo']]

studio_dup = {}

while currentp <= maxp:
  log.info("Getting page %s of %s..." % (currentp, maxp))

  listing = 'https://' + args.site + '/studio_list_0_' + str(currentp) + '.html'
  try:
    resp = session.get(listing)                    # get the protected page
    if resp.status_code == 200:
      #print(resp.text)
      soup = BeautifulSoup(resp.text, "html5lib")
    else:
      log.error("Return Code %s" % str(resp.status_code))
  except Exception  as e:
    log.error("%s" % str(e))
  for rows in soup.find_all('td', attrs={'width':'250'}):
    for a in rows.findAll('a'):
      studio_text = re.sub('DVD Movies', '', a.text)
      studio_text = re.sub(r'[\ \n]{2,}', '', studio_text) 
#      print (studio_text)

      if studio_text.upper() in studio_dup.keys():
        logging.debug("Duplicate studio found: %s", studio_text)
      else:
      # Write Record
        logging.debug("Appending %s", studio_text)
        listings.append([studio_text, studio_text])
      # Add duplicate cache
        studio_dup[studio_text.upper()] = ""
#      pprint.pprint(listings)
  currentp = currentp + 1
  time.sleep(3)
# print(listings)

# Write to CSV
with open(args.csvfile, 'a', encoding='utf-8') as toWrite:
  writer = csv.writer(toWrite)
  writer.writerows(listings)

