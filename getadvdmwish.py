#!/opt/local/bin/python3

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
parser.add_argument('-c', dest='csvfile', default='./advdmwish.csv', help='Override the CSV file.') 
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
maxp = 1
# Beautiful Soup buffers
soup = None
soupdata = None
# Listings found
if testing:
  listings = [] # Can be filled with a lists of data
else:
  listings = [['Name', 'Studio', 'Price', 'Comment', 'URL']]

# Pull up first page to get info on sizes and limits
if not testing:
  listing = 'https://' + args.site + '/xcart/adult_dvd/alerts.php?order_by=title&seller_login=&page=' + str(currentp)
  try:
    resp = session.get(listing)                    # get the protected page
    if resp.status_code == 200:
  #    print(resp.text)
      soup = BeautifulSoup(resp.text, "html5lib")
      # Get page total
      soupdata = soup.find_all(attrs={'class': 'col-sm-3 results'})
  #    pprint.pprint(soupdata[0])
      if soupdata[0]:
        pages = re.findall(r'\s\d+', str(soupdata[0])) 
        if pages[1]:
          maxp = int(pages[1])
          log.debug("Found maxp of %s" % str(maxp))
        else:
          log.error("Cannot get page index (number not found).")
          sys.exit(1)
      else:
        log.error("Cannot get page index (HTML element not found).")
        sys.exit(1)
  
  # Now that we have the basic scraping info, lets run through the pages
#      maxp = 1
      while currentp <= maxp:
  		# Get the current page
        log.info("Getting page %s of %s..." % (currentp, maxp))
  
        listing = 'https://' + args.site + '/xcart/adult_dvd/alerts.php?order_by=title&seller_login=&page=' + str(currentp)
        try:
          resp = session.get(listing)                    # get the protected page
          if resp.status_code == 200:
  #    print(resp.text)
            soup = BeautifulSoup(resp.text, "html5lib")
          else:
            log.error("Return Code %s" % str(resp.status_code))
        except Exception  as e:
          log.error("%s" % str(e))
        # Process the page  
        foundcomment = False
        foundnew = False
        name = None
        studio = None
        price = None
        comment = None
        url = None
        # Ok, this is a messy bit of state machine. 
        # We start in the loop seeing if we found an existing entry already. 
        # If so we look for a comment in the next TR.
        # If the comment was found we update the comment field, write the entry and reset the flags.
        # If the comment wasn't found, we write out what we have (without the comment), and reset the flags.
        # If no flags were set, we are looking for a TR that may have a listing.
        for rows in soup.find_all('tr'):
          # We found a listing in the previous TR
          if foundnew:
            log.debug("In foundnew...")
            # Search for comment
#            pprint.pprint(rows)
            maybecomment = rows.find_all('font', attrs={'color':'#0000FF'})
#            pprint.pprint(maybecomment)
            if len(maybecomment) > 0:
              foundcomment = True
            # We found the comment. Write and reset.
            if foundcomment:
              log.debug("In foundcomment...")
              # Update comment
              comment = maybecomment[0].get_text()
              comment = comment.replace(u'\xa0', u' ')
              comment = comment.replace(' - ','')
              # Write Record
              logging.debug("Appending %s", [name, studio, price, comment, url])
              listings.append([name, studio, price, comment, url])
#              pprint.pprint(listings)
              # Reset flags
              foundcomment = False
              foundnew = False            
              name = None
              studio = None
              price = None
              comment = None
              url = None
              continue
            # We didn't find the comment. Write what we have and eeset.
            else:
              log.debug("In reset else...")
              if rows.find_all('td', attrs={'colspan':'6'}):   
                # Write Record
                logging.debug("Appending %s", [name, studio, price, comment, url])
                listings.append([name, studio, price, comment, url])
#                pprint.pprint(listings)
                # Reset flags
                foundcomment = False
                foundnew = False 
                name = None
                studio = None
                price = None
                comment = None
                url = None
              # Next
              continue
            # Search for a new listing, and populate the flags and what entries we can
          else:
            log.debug("In search...")
#            pprint.pprint(rows)
            if rows.find_all('td', attrs={'colspan':'6'}):      
              # Reset as we are in a new entry
              foundcomment = False
              foundnew = False
              name = None
              studio = None
              price = None
              comment = None
              url = None
#            maybe = rows.find_all('td')[2]
            else:
              # Findrows with the following attribs -- one should be the URL/Title TD 
              items = rows.find_all('td', attrs={'align':None, 'valign':'top'})
#              pprint.pprint(items)
              for item in items:
                # In that TD look for the link
                titletmp = item.find('a', href=re.compile("dvd_view"))
                if titletmp:
                  foundnew = True
                  name = titletmp.get_text()
#                  pprint.pprint(name)
                  url = 'https://' + args.site + titletmp.get('href')
#                  pprint.pprint(url)
                # In that same TD item harvest studio
                studiotmp = item.get_text().split('  ')
#                pprint.pprint(studiotmp)
                if len(studiotmp) > 1:
                  studio = studiotmp[1]
                  studio = studio.replace('\n','')
                # Stepping up one level ligher look for the TD with the price
                pricetmp = rows.find('td', attrs={'align':'center', 'nowrap':'nowrap', 'valign':'top'})
                if pricetmp:
                  price = pricetmp.get_text()
                  if 'No Listings' not in price:
                    price = re.sub('[^0-9\.\$NoListng]+', '', price)
                # Comment will be in the next TRs
                comment = None
              else:
                continue
        currentp = currentp + 1
        time.sleep(3)
    else:
      log.error("Return Code %s" % str(resp.status_code))
  except Exception  as e:
    log.error("%s" % str(e))
# print(listings)

if args.reset:
  #['Name', 'Studio', 'Price', 'Comment', 'URL']
  for idx in range(len(listings)):
    entry = listings[idx]
    old_entry = copy.copy(entry)    
    float_rating = None     # Extracted rating from comment
    comment_parts = None    # Extracted/split commment
    update_found = False    # Flag to note update status
    oop_found = False       # Flag for Out of Print
    silence_email = False   # Flag to suppress e-mail
    logging.debug("%s", entry)
    if entry[0] == 'Name':
      logging.debug("Skipping header row")
    else:
      if entry[3]:
        # Check for a valid float (5.0 - 0.0), not throw warning
        comment_parts = entry[3].split()
        try:
          float_rating = float(comment_parts[0])
        except ValueError:
          print("Warning: No properly formatted rating found for title", entry[0], "-", entry[1])
        else:
          # Check for a valid float in multiples of .25
          if Decimal(float_rating) % Decimal('0.25') != Decimal('0.0'):
            print("Warning: Rating is not a multiple of 0.25 for title", entry[0], "-", entry[1]) 
      # No comment found
      else:
        print("Warning: No comment/rating found for title", entry[0], "-", entry[1])
      # Check if Price is Null or 'No Listings' and if so set a OOP? flag in the comment field
      if entry[2] is None or 'No Listings' in entry[2]:
        logging.debug("No availbility for title: %s", entry[0])
        if entry[3]:
          if "OOP" not in entry[3]:
            entry[3] = entry[3] + " OOP?"
        else:
           entry[3] = "OOP?"
      if entry[3] is not None:
        if "OOP" in entry[3]:
          oop_found = True
      # Change in place the value of entry
      listings[idx] = entry
      if old_entry != entry:
        logging.debug("Replacing %s", old_entry)
        logging.debug("With      %s", entry)
      # If float is below the threshold, make sure the "don't e-mail flag is set", and the record updated.
      logging.debug("%s", float_rating)
      if float_rating:
        if float_rating < float(args.reset):
          if not oop_found:
            silence_email = True
      # Auto-remove, Send Alerts, and Comments
      if silence_email:
        logging.debug("Will silence.")
      else:
        logging.debug("Will update.")
      rem = re.search('dvd_view_(\d.*)\.html', entry[4])
      if rem:
        sku = rem.group(1)
        logging.debug("SKU: %s", sku)
        up_url ='https://' + args.site + '/xcart/adult_dvd/alerts.php'
        logging.debug(up_url)
        up_values = { 'action': 'add', 'adult_dvd_id': sku, 'page': '1', 'alert': '1', 'auto_delete': '1', 'comment': '' } 
        if silence_email:
          up_values['alert'] = '0'
        if entry[3]:
          up_values['comment'] = entry[3]
        logging.debug("up_values: %s", up_values)
        try:
          resp = session.post(up_url, data=up_values)    # perform the login
          if resp.status_code == 200:
            None
          else:
            log.error("Return Code %s" % str(resp.status_code))
          time.sleep(2)
        except Exception as e:
          log.error("%s" % str(e))
      else:
        logging.error("Could not find sku from URL %s", entry[4])
      
# Write to CSV
with open(args.csvfile, 'a', encoding='utf-8') as toWrite:
  writer = csv.writer(toWrite)
  writer.writerows(listings)

