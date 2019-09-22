#!/usr/bin/python
import sys
sys.path.append("/usr/local/lib/python2.7/site-packages")
import argparse
import copy
import os
import re
import subprocess
#import stat
#import magic
# brew install libmagic
# via pip install python-magic
# export PYTHONPATH=/usr/local/lib/python2.7/site-packages
#from magicfixup import magicfixup
#from datetime import datetime

# Temporary file extension
temp_ext        = ".tmp"

# Parser setup
parser = argparse.ArgumentParser(description='Given a file of filenames, search for strings, and sort output.')
parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-o', dest='outfile', default=False, help='Output the sorted data to this file.')
parser
parser.add_argument('-i', dest='infile', default=False, help='Read this list of files from this file.') 
parser.add_argument('-s', dest='strings_exec', default='/usr/bin/strings', help='Override the full path to the strings binary.')
parser.add_argument('-g', dest='grep_exec', default='/bin/grep', help='Override the full path to the egrep-compatible grep binary.') 


# True out arg parser
args = parser.parse_args()

# Make sure one of the primary validation modes is set
if (not args.infile or not args.outfile ):
  parser.print_help()
  print "\n"
  print "Error: Need both the infile and the outfile supplied."
  sys.exit(1)
else: None

if not os.access(args.strings_exec, os.X_OK):
  print "Error: Supplied path to strings was not found/executable."
  sys.exit(1)

if not os.access(args.grep_exec, os.X_OK):
  print "Error: Supplied path to grep was not found/executable."
  sys.exit(1)

include_strings = ['madam', 'bookmark', 'chris', 'mcclusk', 'vidch', 'tekno', 'technodude']
exclude_strings = ['wChk', 'checkbox', 'checkboxes', 'checkmark', 'Christmas', 'checkerboard', 'checksum type %s', 'check slice %s', 'ChristophER', 'checkDisk:withFormat:', 'Christopher Moore', 'check-am: all-am', 'check: check-am', 'BookmarksSearchBar', 'mADAM', 'tEKNo', 'tEKNo\O', 'cHRIs', 'BOOKMARK', 'cHRIS^LOR', ' Bookmark:(109,26)', 'bookmark:(136,86)', 'bookmarkVal:(3,62)', 'VidcHE', 'mAdamA', 'BookmarkInsert', 'Bookmark Menu Commands', 'bookmarks, defining', 'bookmarks, deleting', 'bookmarks, removing', 'vidchH', 'Christ', 'Bookmark saving failed (%s)', 'bookmark-goto', 'bookmark-save', 'bookmark_get_filename', 'bookmarks-changed', 'BookmarkOnCloseW', 'Bookmark not defined.', 'Bookmark Color', 'Bookmark has no corresponding address in database', 'Christoph', 'Bookmarks\v1\Count', 'Teknologisk Institut', 'Teknoids', 'Chris Forkin Consulting', 'Christos', 'Chris, are we still using Qwest?', 'Chris, just a reminder for you to add on those last 2.', '# Chris is there something we can setup for Lori so she doesn\'t have to depend', 'Bookmark:(109,26)', 'BOOKMARK_ID', 'BOOKMARK_ID', 'vidCH', 'madam ]' ]
exclude_fuzzy = ['2:32:00::', '1:04:00::', '1:14:00::', '1:09:0', '3:01:00::', '1:20:0', '1:16:00::', '1:11:00::', '1:18:01::', '1:06:00::', 'Christophe Casalegno', 'JIMMY_CHEN@fic.com.tw', 'Roubekas', 'Chris Scott', 'christopher pickert', 'Chris Petrell', 'Chris McKeever', 'Christoph Badura', 'Chris Rutledge', 'Chris Nicholls', 'Christoph Kaegi', 'Chris Lawder', 'Chris Smith', 'Chris Garrigues', 'Chris Cejka', 'christoph.beyer@desy.de', 'Christoph Kaegi', 'Christoph Peus', 'Christopher Robinson', 'chris.robinson@voipsupply.com', 'Christopher Welsh', 'chris rothgeb', 'Chris Ong', 'Chris Cameron', 'Chris Snider', 'Christelle Ronce', 'Chris Garrigues', 'Botha', 'Christoffer Dahl Petersen', 'Chris Trown', 'Chris Hobbs', 'Christoph Galuschka', 'fic.com.tw', 'Chris.Im@ribbit.com', 'Chris Tepaske', 'Chris Rondthaler', 'Chris Roubekas', 'Chris Garrigues', 'Chris S.', '.nib', ' is uptodate', 'f?sd', 'Mh@l', 'Christer Solskogen', 'Chris Odell', 'Christopher Kelley', 'Chris Costello', 'Christopher Nehre', 'randomcamel.net', 'Chris Laverdure', 'Chris McCluskey wrote:', 'Chris,', 'Chris Munson', 'CHRISCHU', 'CHRISJ', 'Chris Brooks', 'Chris Fuhrman', 'Chris Josephes', 'Chris Phillips', 'Chris Radcliff', 'Christoph T. Traxler', 'Christopher Berning', 'chris@clotho.com', 'chris@globalspin.com', 'chrisj@mr.net', 'Christopher Maloney', 'Christopher White', 'CHRISC', '-49', 'Christoph Adomeit', 'allow quick connection', 'chrisc@classic-cable.com', 'chris.vanname@twcable.com', 'chris.downing@cox.com', 'Chris Van Name', 'Chris Patterson', 'Chris Ginn', 'Chris Fox', 'Chris Farris', 'Chris Berry', 'Christlicher', 'Chris Graham', 'Christopher Durang', 'Christopher Murphy', 'Chris Graham', 'Chris Yu', 'Chris Holland', 'CHRISTOPHER CECILANI', 'CHRISTOPHER L SUDA', 'CHRISTOPHER W HUGHES', 'Chris Peters', 'CHRISTOFFERSEN/GREGG', 'CHRISTPHR S ROEMER ', 'CHRISTOPHER HOWARD', 'CHRIS JOHNSEN', 'Chris McQuinn', 'Chris Gifford', 'Chris Allen', 'Christopher Seiwald', 'christof.koerner@mchr1.siemens.de', 'vidchyxWj', 'Bookmark:(109,26)', 'chris.horlander@wcom.com', 'chris@web.ifish.co.jp', 'Chris Murray', 'Chris Murray', 'Chris Kordish', 'Christopher Alexander', 'McCluskiy', 'McClusky', 'Christopher P Rigano', 'Christopher A. Martin', 'chris.im', 'chris im', 'CHRISTEN', 'chrisSuci', 'Chris Hafey', 'Chris Mley', 'christer.holmberg@lmf.ericsson.se', 'chrissy@entercomp.com', 'Christopher P Rigano', 'Christer', 'Chris Larsen', 'Chris Horak', 'Chris Ungson', 'christof.koerner@mchr1.siemens.de', 'chris.horlander@wcom.com', 'Christof', 'Christopher Mik', 'Chris Bowick', 'christen', 'Chris Moore', 'Chris Jacobsen', 'Chris...', 'cjm4@lucent.com', 'bookmark:p(0,34)', 'bookmark:(0,49)', 'bookmark:p(0,33)', 'bookmark:p(0,35)', 'bookmarkname:(0,21)', 'bookmarkname:p(10,36)', 'Chris Kennedy', 'cached directory listings', 'Bookmark:(109,26)', 'Chris Allen', 'Bookmark reject', 'chris.woodard@genband.com', 'Chris Woodard', 'Chris Newman', 'Chris.Newman', 'Chris Bagwell', 'Munir', 'Chris Morgan', 'Chris Ellmore', 'Chris Mills', 'Christer Ho', 'Christopher Plabl', 'Chris Phillips', 'Chris Van Name', 'Chris Ginn', 'Chris Farris', 'Chris Rohrer', 'Chris Leishman', 'Chris Uzdavinis', 'Chris Zimman', 'Christoph Poggemann', 'Christopher Kohlhoff', 'Brian Masney', 'Chris Mills', 'Chris Ungson', 'Chris Allen', 'Chris Byrd', 'chris yarrington', 'Chris Bowick', 'Chris Hogg', 'Madamanchi', 'patch retrieval', 'B0', 'b1', '7040', 'Shahar Noy', 'chris.chen@gateway.com', 'Christ Presbyerian', 'Christoph Herdeg', 'chrisd@better-investing.org', 'Chris McKinnon', 'bookmarks are present', 'Christopher Peter Welsh', 'Christopher Kalos', 'christlike', 'christop caesar', 'Bookmark us now', 'chris laconic', 'Stephen Makishima', 'smakishima@digitaldeck.com', 'Chris McCluskey wrote', 'chrissake.', 'Christ!', 'Christ,', 'Christopher Bentley', 'chrisdown', 'chrissoft', 'Chris Runge', 'Chris Hafey', 'christer.holmberg@lmf.ericsson.se', 'chris@infravast.com', 'Chris Hogg', ' Chris Larsen', 'Chris Russell', 'Chris Rogness', 'Chris Packard', 'Chris Murray', 'Chris Mikkelson', 'chris yarrington', 'Christopher Gill', 'chris@infravast.com', 'Christopher P Rigano', 'Christer Ho', 'who will handle the maintenance agreement', 'Chris_Zhong', 'Christos', 'Gilbert', 'missing from the list of materials', ' who will handle the maintenance agreement', 'Chris and Nicole', 'Chris (Lance) Gilbert', 'Chris Hedley', 'Chris Ryan', 'Chris Neustrup', 'Chris Blizzard', 'Chris C.', 'Chris schrieb', 'chris verges', 'Chris Slack', 'dierkens.com', 'Chris Ricks', 'Chris Tepaske', 'schrieb', 'Chris J. Bottaro', 'chris@gensler.to', 'Chris Smith', 'Christoph Klein', 'Chris Bailey', 'Christopher Moss', 'Chris Hobbs', 'Chris Walton', 'chrissylight@mda.org.il', 'janja', 'jerrychuang', 'jank@digitaldeck.com', 'Bryan Grziwok', 'Chrissi', 'Bookmark names preceded by a', 'bookmark-default-file, which is', 'Chris Reynoso', 'Christopher William Klaus', 'Christopher Klaus', 'Christy', 'Chrisvangogh@hotmail.com', 'by clicking on the column headings', 'Chris Ollis', 'chris.summers@gtri.gatech.edu', 'Chris BeHanna', 'chris@bogus.behanna.org', 'chris@scary.beasts.org', 'Chris Paget', 'Chris Green', 'chris@haakonia.hitnet.rwth-aachen.de', 'Chris Knight', 'chris@terminal.at', 'Chris Covell', 'Christopher Mann', 'Chris Umphress', 'Christey', 'Christopher Kr', 'Chris Goodwin', 'Kukulies', 'Chris Schreiber', 'Paget', 'Chris Wright', 'Christoph Sold', 'chrismcc@pricegrabber.com', 'Christopher McCrory', 'Chris Gilbert', 'Christer Oberg', 'Chris Norton', 'Christopher Ess', 'Chris Bellers', 'chrisw@pacaids.com', 'Christer Palm', 'Chris Johnson', 'Chris Ess', 'Christoph Jeschke', 'Chris Knight', 'Chris Merkel', 'Chris Hurley', 'W. Klaus', 'Chris Huebsch', 'Kulish', 'Chris Candreva', 'Christopher Fillion', 'Christopher T. Beers', 'Christopher All', 'Chris Shenton', 'bookmark name, type C-w while setting a bookmark.  Successive C-w', 'bookmark with name NAME would be the one in effect at any given time,', 'bookmarks already present in your Emacs, the new bookmarks will get', 'bookmarks.  See help on function', 'BookmarkAgent', 'bookmark_agent_', 'Chris Urmson', 'bookmark_add', 'bookmarksScrollPosition', 'Chris Halls', 'Chris Phelps', 'goodies.xfce.org/projects/applications', 'Christophe Bisi', 'Chris Urmson', 'Christopher York', 'Christopher Davis', 'Christopher Chan-Nui', 'Christophe Grosjean', 'Christoph Lamprecht', 'Chris Williams', 'Chris Wick', 'Chris Tubutis', 'Chris Pepper', 'Chris Lightfoot', 'Chris Dolan', 'Chris Bongaarts', 'Chris Ball', 'bingosnet.co.uk', 'chrisfer@us.ibm.com', 'Christchurch', 'Chris Willis', 'Chris Lilley', 'Chris Rodriguez', 'chrisfer@us.ibm.com', 'Chris Fitzpatrick', 'Chris Burnley', 'Chris Crawford', 'Chris Gormont', 'Christopher Thompson', 'Chris Robinson', 'Christopher Cross', 'Chris Martin', 'chris@xten', 'Christner Renee', 'Chris Liberti', 'Chris Pureka', 'drewsf77@yahoo.com', 'Chris Isaak', 'Chris Raff', 'Chris Dugan', 'Christopher Johnson', 'Christophe Mutricy', 'Christof Baumgaertner', 'Chris Clepper', 'Chris Bentley', 'Chris Lilley', 'Christophe Tronche', 'Christopher Seawood', 'Christopher Hoess', 'Christopher A. Aillon', 'Chris McAfee', 'bookmarkDialog.setContentWidth', 'Christoph Sch', 'Chris Hondl', 'Christos S. Zoulas', 'Chris Kingsley', 'Chris Grevstad', 'Chris Jefferson', 'Christopher Oliver', 'Christoph Loeffler', 'Chris Rowley', '1:18:00::', 'Chris Hofstader', 'sprout@dok.org', 'Christophe Schlick', 'Christopher L Cheney', 'Christopher Yeoh', 'Christopher R. Hawks', 'Chris Demetriou', 'Chris Murphy', 'Christopher Hoover', 'Christof Ullwer', 'Christopher Davis', 'Christoph Wedler', 'Chris Bone', 'Chris Pollard', 'Chris Baldwin', 'Christos Zoulas', 'Chris, the Young One' ,'Chris Saia', 'Chris D. Peterson', 'Chris Peterson', 'Christoph Pfisterer', 'Chris D.', 'Chris Kent', 'Chris Burleson', 'chris rodre', 'Christophe Papazian', 'Christoph Ludwig', 'Chris Sawer', 'Chris Jackson', 'Christophe Kalt', 'Chris Ransom', 'Chris Metcalf', 'Chris Arthur', 'christos@theory.tn.cornell.edu', 'Christopher Johnson', 'Christophe Mutricy', 'Christof Baumgaertner', 'Chris Clepper', 'Christophe Devine', 'Christopher Seip', 'Christoph Thielecke', 'Chris Jefferson', 'Christos S. Zoulas', 'Chris Kingsley', 'Chris Grevstad', 'Christos Zoulas', 'Christopher Titus', 'Chris Young', 'cobalt555@earthlink.net', 'Christophe Achard', ' Chris Urmson', 'Chris Rankin', 'Chris French', 'Chris Jasper', 'Chris McCarty', 'Christopher Stone', 'Chris Ricker', 'Chris Burkhalter', 'Chris Brown', 'Chris E. Martin', 'Christopher J. White', 'Christopher Andrew Spiking', 'Chris Zwilling', 'Christoph Lossen', 'Chris Covington', 'Christopher Vance', 'Chris Provenzano', 'Chris Achilleos', 'kdmgreet.mo', 'Christophe Fergeau', 'Chris Lalancette', 'Chris Petersen', 'ChristCongo', 'Chris Lu', 'Chris Lalancette', 'chris.stone@gmail.com', 'rpm@forevermore.net', 'kaboom@oobleck.net', 'Chris Ridpath', 'chris.ridpath@utoronto.ca', 'Christopher Warner', 'zanee@kernelcode.com', 'Christopher R. Gabriel', 'Christopher J. Lahey', 'Christophe Merlet', 'Christophe Fergeau', 'Chris Toshok', 'Chris Phelps' 'Chris Halls', 'Christopher Molnar', 'molnarc@mandrakesoft.com', 'Chris Kloiber', 'ckloiber@redhat.com', 'Chris Evans', 'chris@ferret.lmh.ox.ac.uk', 'BookmarkCallback', 'Chris Grau', 'chris@chrisgrau.com', 'Christoph Ma', 'adam@spicenitz.org', 'Christoph Spalinger', 'Chris Nandor', 'Chris Wolstenholme', 'Christopher J. White', 'Christopher Andrew Spiking', 'Chris Zwilling', 'Chris St. Pierre', 'Christopher Vance', 'Chris Evans', 'Chris Paultrie', 'Chris Jasper', 'Chris Brown', 'Bookmark saving failed (%s)', 'Bookmark saving failed: %s', 'Christoph Michel IT Management', 'Christoph Anderegg', 'Chris Rauschuber', 'Chris Abernethy', 'bookmark:(136,86)','Chris Gugger', 'Christopher K. St. John', 'Christoph Wiest', 'Christoph Neusch', 'Chris Wilson', 'Chris Waters', 'Chris Maynard', 'Chris Jepeway', 'Christer Holmberg', 'Chris Im', 'Chris Maloney', 'Christopher Vickery', 'Christopher T. Johnson', 'Chris Allegretta', 'Christopher M. Ward', 'Chris Mason', 'Chris Adams', 'Chris Dent', 'Christophe Colle', 'Christopher James', 'BOOKMARK:t', 'Chris Reidenouer', 'camut', 'Christopher Blizzard', 'Chris Ding', 'Christoph Litauer', 'Chris Ransom' 'Chris Metcalf', 'Chris Hopps', 'Chris G. Demetriou', 'Chris F.M. Verberne', 'Chris Arthur ', 'stentorsoft.com', 'CHRIS PIZZELLO', 'Christmas' 'Chris Hafey', 'Schlaeger', 'christmas', 'Dawe', 'Delmas', 'Christopher Cotton', 'fbsd', 'Christmas Island', 'christian', 'ports-supfile', 'ng_one2many.ko', 'Christopher Aillon', 'Christoph Wickert', 'Christoph Maser', 'Christian Persch', 'Chris Weyl', 'Christof Damian', 'Chris Faylor', 'Chris J. Bednar', 'Lesniewski', 'Sylvain', 'Chris Yeo', 'Christi', 'Christopher Meng', 'Christoph Ganser', 'Chris Feist', 'ChristmasIsland', 'Chris Botti', 'Chris Lumens', 'Schaller', 'Christine', 'christnet', 'Christopher Allion', 'Chris Eagle', 'Chris Heath', 'Christensen', 'Christoph Lameter', 'Chris P. Ross', 'Christoph Hellwig', 'Christoph Lameter', 'Teknor', 'Christie', 'Carline', 'Chris Leach', 'Chris Mungall', 'Chris Prather', 'Chris Thompson', 'Christian H. Geuer-Pollmann', 'Christophe Dehaudt', 'Christopher J. Madsen', 'Chris Wing' ]

# Open input fileq
if args.infile:
  try:
    inf = open(os.path.abspath(args.infile))
  except IOError:
    print "Error: Cannot open inputfile %s for reading." % (args.infile)
    sys.exit(1)

# Open output file
if args.outfile:
  try:
    outf = open(os.path.abspath(args.outfile), 'w')
  except IOError:
    print "Error: Cannot open outfile %s for writing." % (args.outfile)
    sys.exit(1)

# Prep "grep"
search_re_string = '|'.join(include_strings)
search_re = re.compile(search_re_string, re.IGNORECASE)

# Get next test file from the input file
for tfile in inf:
  tfile = tfile.strip('\n')
  tfile_full = os.path.abspath(tfile)
  if os.access(tfile_full, os.R_OK):
# Get strings
    strings_buffer = subprocess.check_output([args.strings_exec, tfile_full])
    strings = strings_buffer.split('\n')
# Grep through strings and put matches into an array
    matches = []
    for possible in strings:
      if search_re.match(possible):
        matches.append(possible)
# Remove duplicates in the array and remove the excludes
    matches = list(set(matches) - set(exclude_strings))
# Futher filter with other case insentisitve matches
    temp_matches = copy.deepcopy(matches)
    for item in temp_matches:
      for searchitem in exclude_fuzzy:
        search_re_again = re.compile(searchitem, re.IGNORECASE)
        if search_re_again.search(item):
          print("Remove: %s" % item)
          try:
            matches.remove(item)
          except:
            pass
# Sort the array
    matches.sort()
# If the size of the array > 0
    if len(matches) > 0:
## Print the file + <CRLF>
      outf.write("%s\n" % tfile)
## For each item in the array
      for match in matches:
### Print a # and then the string and then <CRLF>
        outf.write("# %s\n" % match)
      outf.flush()
  else:
    print "Error: Cannot read test file %s" % tfile_full

# Close the output file
if outf:
	outf.flush()
	outf.close()

# Close the input file
if inf:
        inf.close()
