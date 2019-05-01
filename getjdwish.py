#!/opt/local/bin/python3

import argparse
import csv
import logging
import operator
import os
import pprint
import re
import requests
import sys
import time
from bs4 import BeautifulSoup

# Parser setup
parser = argparse.ArgumentParser(description='Pull wish list from a known website, and export the wishlist to a CSV file.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-c', dest='csvfile', default='./jdwish.csv', help='Override the CSV file.') 
parser.add_argument('-u', dest='user', default=False, required=True, help='Website user.')
parser.add_argument('-p', dest='pswd', default=False, required=True, help='Website user\'s password.')
parser.add_argument('-S', dest='site', default=False, required=True, help='Website URL.')

# True out arg parser
args = parser.parse_args()

# Set up the logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
log = logging.getLogger(__name__)
##for lh in ("pynoc", "pynoc.apc", "paramiko", "paramiko.transport"):
##    logging.getLogger(lh).setLevel(100)

if os.path.exists(args.csvfile):
  os.remove(args.csvfile)
    
# Setup Requests Handle and Params
requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.5) Gecko/20041111 Firefox/1.0'})
session.headers.update({'Accept-Encoding': 'x-gzip'})
session.headers.update({'Accept': 'text/html, application/xml'})

# Do login
login = 'https://' + args.site + '/login/'
try:
  resp = session.get(login)    # retrieve cookie, tokens, and other stuff
  if resp.status_code == 200:
    None
  else:
    log.error("Return Code %s" % str(resp.status_code))
except Exception as e:
  log.error("%s" % str(e))

values = { 'username': args.user, 'userpwd': args.pswd, 'login_hit': 'true' }
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

# Beautiful Soup buffers
soup = None
soupdata = None
title = None
titledata = None

listings = [['Name', 'Studio', 'Price', 'URL']]

# Did we get good data
validpage = 1
while validpage:
# Get the current page
  log.info("Getting page %s..." % (currentp))
  listing = 'https://' + args.site + '/porn-movies/seite/' + str(currentp) + '/?show=wishlist'
  try:
    resp = session.get(listing)                    # get the protected page
    if resp.status_code == 200:
#      print(resp.text)
      soup = BeautifulSoup(resp.text, "html5lib")
      # Process the page
      soupdata = soup.select("div[class*='search_list_item']")
#      pprint.pprint(soupdata)
    else:
      log.error("Return Code %s" % str(resp.status_code))
  except Exception  as e:
    log.error("%s" % str(e))
  if soupdata:
    for title in soupdata:
      name = None
      studio = None
      price = None
      url = None
      titledata = title.find('h4')
#      pprint.pprint(titledata)
      name = titledata.find('a').text.replace(' (DVD)','').replace('  ',' ')
      if titledata.find('a')['href']:
        url = 'https://' + args.site + titledata.find('a')['href']
      titledata = title.find('span', {'class': 'fsize12'})
      studio = titledata.text
      titledata = title.find('span', {'class': 'fsize14 strong'})
      price = titledata.text.replace('From ','')
      price = price.replace('Items already sold','')
      # Write Record
      if name:
        listings.append([name, studio, price, url])
      else:
        log.error("Skipped a title. Bad data?")
#        pprint.pprint(listings)
    currentp = currentp + 1
    time.sleep(3)
  else:
    validpage = 0 

sortedlistings = sorted(listings, key=operator.itemgetter(0))
# Write to CSV
with open(args.csvfile, 'a', encoding='utf-8') as toWrite:
  writer = csv.writer(toWrite)
  writer.writerows(sortedlistings)

