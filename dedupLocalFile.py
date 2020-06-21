#!/opt/local/bin/python3

#TODO
#Add aggressive checking of serial items
#Use Trash folder 
#Add trial mode to preview destructive changesb
#Use a form loop pattern to allow for multiple pattern matches
#Pick a serial pattern for non-duplicate files what would hash to an exising name


# Starts with:
# 'Copy of '
# 'Copy (NN) of '

# Contains:
# .Id_NN 

# Ends with:
# ' copy' 
# ' copy N'
# -(NNNNN)
# ' (NN)'
# (NN)   

import argparse
import errno
import hashlib
import os
import pprint
import re
import shutil 
import sys


#def mkdir_p(path):
#  try:
#    os.makedirs(path)
#  except OSError as exc: 
#    if exc.errno == errno.EEXIST and os.path.isdir(path):
#      pass
#    else:
#      raise

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

# Parser setup
parser = argparse.ArgumentParser(description='Looks for duplicate files and remove the duplicate if a source is found.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Verbose reporting.')
parser.add_argument('items', nargs='+', default=None)

# True out arg parser
args = parser.parse_args()

# Exspand argument list
for item in args.items:
  if item == '*':
    if len(args.items) > 1:
      print("Error: Cannot mix an escaped * and other arguments")
      sys.exit(1)
    else:
      args.items=[]
      for root, dirs, files in os.walk(os.getcwd()):
        for f in files:
          args.items.append(os.path.join(root,f))

for item in args.items:
  original = item
  original_sum = cksum(item)
  if args.debug:
    print("Original: %s" % original )
    print("Original: %s" % original_sum )
  deleted = False

  # .Id_NN 
  re_Id = re.compile(r'\.Id_[0-9]+\.')
  done = False
  while not done and not deleted:
    if re_Id.search(item):
#      print("Here")
      if args.debug:
        print("In: re_Id")
      itemtest = re_Id.sub('.', item)
      if original == itemtest:
        print("Warning: Regex failed in re_Id")
        done = True
      else:
        item_sum = cksum(itemtest)
        if args.debug:
          print("New Item: %s" % itemtest )
          print("New Item: %s" % item_sum )
        if original_sum == item_sum:
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue 
    else:
      done = True

  # 'Copy of '
  re_CopyOf = re.compile(r'^Copy\sof\s', flags=re.IGNORECASE)
  done = False
  while not done and not deleted:
    if re_CopyOf.match(item):
      if args.debug:
        print("In: re_CopyOf")
      itemtest = re_CopyOf.sub('', item)
      if original == itemtest:
        print("Warning: Regex failed in re_CopyOf")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue
    else:
      done = True  

# 'Copy (NN) of '
  re_CopyOfParen = re.compile(r'^Copy\s\([0-9]+\)of\s', flags=re.IGNORECASE)
  done = False
  while not done and not deleted:
    if re_CopyOfParen.match(item):
      if args.debug:
        print("In: re_CopyOfParen")
      itemtest = re_CopyOfParen.sub('', item)
      if original == itemtest:
        print("Warning: Regex failed in re_CopyOfParen")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue
    else:
      done = True

# ' copy' 
  re_CopyEnd = re.compile(r'\scopy\.', flags=re.IGNORECASE)
  done = False
  while not done and not deleted:
    if re.match(r'\.Id_[0-9]+\.', item):
      if args.debug:
        print("In: re_CopyEnd")
      itemtest = re_CopyEnd.sub('.', item)
      if original == itemtest:
        print("Warning: Regex failed in re_CopyEnd")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue
    else:
      done = True

# ' copy N'
  re_CopyEndCount = re.compile(r'\scopy\s[0-9]+\.', flags=re.IGNORECASE)
  done = False
  while not done and not deleted:
    if re_CopyEndCount.match(item):
      if args.debug:
        print("In: re_CopyEndCount")
      itemtest = re_CopyEndCount.sub('.', item)
      if original == itemtest:
        print("Warning: Regex failed in re_CopyEndCount")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue
    else:
      done = True

# -(NNNNN)
  re_EndCountDashParen = re.compile(r'\-\([0-9]+\)\.', flags=re.IGNORECASE)
  done = False
  while not done and not deleted:
    if re_EndCountDashParen.match(item):
      if args.debug:
        print("In: re_EndCountDashParen")
      itemtest = re_EndCountDashParen.sub('.', item)
      if original == itemtest:
        print("Warning: Regex failed in re_EndCountDashParen")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue
    else:
      done = True

# ' (NN)' or (NN)
  re_EndCountParen = re.compile(r'\s?\([0-9]+\)\.', flags=re.IGNORECASE)
  done = False
  while not done and not deleted:
    if re_EndCountParen.match(item):
      if args.debug:
        print("In: re_EndCountParen")
      itemtest = re_EndCountParen.sub('.', item)
      if original == itemtest:
        print("Warning: Regex failed in re_EndCountParen")
        done = True
      else:
        item_sum = cksum(itemtest)
        if original_sum == item_sum:
          if args.debug:
            print("New Item: %s" % itemtest )
            print("New Item: %s" % item_sum )
          print("Will remove %s" % original)
          os.remove(original)
          done = True
          deleted = True
        else:
          item = itemtest
          continue
    else:
      done = True

print("DONE.")

