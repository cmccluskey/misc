#!/opt/local/bin/python3

import argparse
import csv
import logging
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
parser.add_argument('-c', dest='csvfile', default='./advdmwish.csv', help='Override the CSV file.') 
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
listings = [['Name', 'Studio', 'Price', 'Comment', 'URL']]

# Pull up first page to get info on sizes and limits
listing = 'https://' + args.site + '/xcart/adult_dvd/alerts.php?order_by=title&seller_login=&page=' + str(currentp)
try:
  resp = session.get(listing)                    # get the protected page
  if resp.status_code == 200:
#    print(resp.text)
    soup = BeautifulSoup(resp.text, "html5lib")
    # Check for wishlist error
#    soupdata = soup.select('div > div > p')
#    if "You don't have any titles in your wishlist at this time." in soupdata[0].get_text():
#      print ("Error: Wishlist empty error")
#      sys.exit(1)
#
#    # Get page total
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
#          pprint.pprint(rows)
          maybecomment = rows.find_all('font')
#          pprint.pprint(maybecomment)
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
            listings.append([name, studio, price, comment, url])
  #          pprint.pprint(listings)
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

            # Write Record
            listings.append([name, studio, price, comment, url])
  #          pprint.pprint(listings)
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
          if len(rows.find_all('td')) >= 6:
            maybe = rows.find_all('td')[2]
#            pprint.pprint(maybe)
            item = maybe.find_all('a')
            if len(item) > 0:
              foundnew = True
              name = item[0].get_text()
              studiotmp = maybe.get_text().split('  ')
#              pprint.pprint(studiotmp)
              if len(studiotmp) > 1:
                studio = studiotmp[1]
                studio = studio.replace('\n','')
              price = rows.find_all('td')[3].get_text()
              comment = None
              url = 'https://' + args.site + item[0].get('href')
            else:
              continue
          else:
            continue  
      currentp = currentp + 1
      time.sleep(3)

  else:
    log.error("Return Code %s" % str(resp.status_code))
except Exception  as e:
  log.error("%s" % str(e))

#pprint.pprint(listings)

# Write to CSV
with open(args.csvfile, 'a', encoding='utf-8') as toWrite:
  writer = csv.writer(toWrite)
  writer.writerows(listings)

