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
parser.add_argument('-c', dest='csvfile', default='./jdwish.csv', help='Override the CSV file.') 
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
# What is the number of pages to read
maxp = 1
# Beautiful Soup buffers
soup = None
soupdata = None
# Listings found
if testing:
  listings = [] # Can be filled with a lists of data
else:
  listings = [['Name', 'Studio', 'Price', 'Comment', 'URL', 'BestVendor']]

# Pull up first page to get info on sizes and limits
if not testing:
  listing = 'https://' + args.site + '/porn-movies/seite/' + str(currentp) + '/?show=wishlist' 
  try:
    resp = session.get(listing)                    # get the protected page
    if resp.status_code == 200:
#      print(resp.text)
      soup = BeautifulSoup(resp.text, "html5lib")
      # Get page total
      soupdata = soup.find_all('ul', attrs={'class': 'dropdown-menu', 'role': 'menu'})
#      pprint.pprint(soupdata)
      if soupdata:
        matches = re.findall('porn-movies.*/(\d+)/\?show\=wishlist', str(soupdata))
        maxp=int(max(matches))
        if maxp: 
          log.debug("Found maxp of %s" % str(maxp))
        else:
          log.error("Cannot get page index (number not found).")
          sys.exit(1)
      else:
        log.error("Cannot get page index (HTML element not found).")
        sys.exit(1)
  
  # Now that we have the basic scraping info, lets run through the pages
      while currentp <= maxp:
  		# Get the current page
        log.info("Getting page %s of %s..." % (currentp, maxp))
        listing = 'https://' + args.site + '/porn-movies/seite/' + str(currentp) + '/?show=wishlist' 
        try:
          resp = session.get(listing)                    # get the protected page
          if resp.status_code == 200:
#      print(resp.text)
            soup = BeautifulSoup(resp.text, "html5lib")
          else:
            log.error("Return Code %s" % str(resp.status_code))
        except Exception  as e:
          log.error("%s" % str(e))
        # Process the page  
        for row in soup.find_all('div', {'class': re.compile(r'^col\-xs\-60\ search_list_item')}):
          name = None
          studio = None
          price = None
          comment = None
          url = None
          vendor = None
          vendortemp = None
          name = row.find('a', { 'class': 'text-default strong' }).get_text()
          if name:
            name = re.sub('\ \(DVD\)', '', name)
            name = re.sub('\s\s', ' ', name)
#          pprint.pprint(name)
          if name:
            url = row.find('a', { 'class': 'text-default strong' }).get('href')
#            pprint.pprint(url)
            if url:
              url = 'https://' + args.site + url  
            price = row.find('span', { 'class': 'fsize14 strong' }).get_text()
            if price:
              price = re.sub('From ', '', price)
              price = re.sub('Items already sold', '', price)
            studio = row.find('span', { 'class': 'fsize12' }).get_text()
          else:
            logging.debug("Cannot find title in row %s", titletemp)           
          # Get the vendor
          if url:
            log.info("Getting title %s for vendor..." % (url))
            vendorsoup = None
            try:
              resp = session.get(url)                    # get the protected page
              if resp.status_code == 200:
#               print(resp.text)
                vendorsoup = BeautifulSoup(resp.text, "html5lib")
              else:
                log.error("Return Code %s" % str(resp.status_code))
            except Exception  as e:
              log.error("%s" % str(e))
            if vendorsoup:
              vendortemp = vendorsoup.find('a', {'href': re.compile(r'^\/user_info\/')})
              if vendortemp:
                vendor = vendortemp.get_text() 
          if name:
            listings.append([name, studio, price, comment, url, vendor])
        currentp = currentp + 1
        time.sleep(3)
    else:
      log.error("Return Code %s" % str(resp.status_code))
  except Exception  as e:
    log.error("%s" % str(e))
pprint.pprint(listings)
#
#if args.reset:
#  #['Name', 'Studio', 'Price', 'Comment', 'URL']
#  for idx in range(len(listings)):
#    entry = listings[idx]
#    old_entry = copy.copy(entry)    
#    float_rating = None     # Extracted rating from comment
#    comment_parts = None    # Extracted/split commment
#    update_found = False    # Flag to note update status
#    oop_found = False       # Flag for Out of Print
#    silence_email = False   # Flag to suppress e-mail
#    logging.debug("%s", entry)
#    if entry[0] == 'Name':
#      logging.debug("Skipping header row")
#    else:
#      if entry[3]:
#        # Check for a valid float (5.0 - 0.0), not throw warning
#        comment_parts = entry[3].split()
#        try:
#          float_rating = float(comment_parts[0])
#        except ValueError:
#          print("Warning: No properly formatted rating found for title", entry[0], "-", entry[1])
#        else:
#          # Check for a valid float in multiples of .25
#          if Decimal(float_rating) % Decimal('0.25') != Decimal('0.0'):
#            print("Warning: Rating is not a multiple of 0.25 for title", entry[0], "-", entry[1]) 
#      # No comment found
#      else:
#        print("Warning: No comment/rating found for title", entry[0], "-", entry[1])
#      # Check if Price is Null or 'No Listings' and if so set a OOP? flag in the comment field
#      if entry[2] is None or 'No Listings' in entry[2]:
#        logging.debug("No availbility for title: %s", entry[0])
#        if entry[3]:
#          if "OOP" not in entry[3]:
#            entry[3] = entry[3] + " OOP?"
#        else:
#           entry[3] = "OOP?"
#      if entry[3] is not None:
#        if "OOP" in entry[3]:
#          oop_found = True
#      # Change in place the value of entry
#      listings[idx] = entry
#      if old_entry != entry:
#        logging.debug("Replacing %s", old_entry)
#        logging.debug("With      %s", entry)
#      # If float is below the threshold, make sure the "don't e-mail flag is set", and the record updated.
#      logging.debug("%s", float_rating)
#      if float_rating:
#        if float_rating < float(args.reset):
#          if not oop_found:
#            silence_email = True
#      # Auto-remove, Send Alerts, and Comments
#      if silence_email:
#        logging.debug("Will silence.")
#      else:
#        logging.debug("Will update.")
#      rem = re.search('dvd_view_(\d.*)\.html', entry[4])
#      if rem:
#        sku = rem.group(1)
#        logging.debug("SKU: %s", sku)
#        up_url ='https://' + args.site + '/xcart/adult_dvd/alerts.php'
#        logging.debug(up_url)
#        up_values = { 'action': 'add', 'adult_dvd_id': sku, 'page': '1', 'alert': '1', 'auto_delete': '1', 'comment': '' } 
#        if silence_email:
#          up_values['alert'] = '0'
#        if entry[3]:
#          up_values['comment'] = entry[3]
#        logging.debug("up_values: %s", up_values)
#        try:
#          resp = session.post(up_url, data=up_values)    # perform the login
#          if resp.status_code == 200:
#            None
#          else:
#            log.error("Return Code %s" % str(resp.status_code))
#          time.sleep(2)
#        except Exception as e:
#          log.error("%s" % str(e))
#      else:
#        logging.error("Could not find sku from URL %s", entry[4])
      
# Write to CSV
with open(args.csvfile, 'a', encoding='utf-8') as toWrite:
  writer = csv.writer(toWrite)
  writer.writerows(listings)

