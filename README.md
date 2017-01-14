The file info tools are designed to build out an extension database, validate that the contents on disk are current with the database, and report/move/fix entries that don't conform to the database.


This procedure is what is used to create the dictionary/database:

Run getfileinfo.py - From a given path in the filesystem, build out a list of files with Magic Descriptions (with minor filtering)

Concatenate all required lists into a single file.

Run normalizefileinfo.py - Build our an extension dictionary with all observed Magic Descriptions. 

Unless the filesystems scanned are 100% correct, you will need to alter the dictionary to eliminiate bad extension -> Magic associations. Found http://www.cleancss.com/python-beautify/ and http://pep8online.com was helpful in locating errors.

Move this dictionary file to dicts/extension.dict

Create/edit dicts/defaultext.dist . This file provides the default extension to be suggested/used when a specific Magic Description is found. This data is folded into the revextension.dict file used in analysis. 

createrevfileinfo.py
 -d debug
 -i Use extension dict
 -f Use default dict
or
 -F Path and filename of default creation of a default dict. 
<create reverse>
<create DEFAULT list>

validatefileinfo.py
 -e extdict
 -m report, move, or rename
 -l log


Other files and directories:

dicts - Directories of python dictionaries common to various scripts.
getfileinfo-README.txt - This document
magicfixup.py - A subroutine to regex around some poorly formatted Magic Descriptions
