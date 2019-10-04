#!/usr/bin/python

import os
import sys

if (sys.argv[1]):
   if (os.path.isdir(sys.argv[1])):
      for (subdir, dirs, files) in os.walk(sys.argv[1]):
         print("%-14s %s" % (str(len(files)),subdir))
else:
   print "ERROR: Root directory not specified.\n"
   sys.exit(1)
