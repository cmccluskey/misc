Misc

FileInfo Tools

The fileinfo tools are designed to identify and remove 1) files that don't appear to be what they represent, and 2) to fix the suffixes of incorrectly labeled files. The tools included here build out an extension database (out of a set of hopefuly "known good",referce filesystems -- or some care in fixing the dicts after running the scripts on a set of "mostly sane" filesystems),  validate that the contents on disk are current with the dictionaries, and report/move/fix entries that don't conform to the dictionaries.


This procedure is what is used to create the dictionary/database:

1. Run getfileinfo.py - From a given path(s) in a filesystem, build out a list of files with Magic Descriptions.

2. Concatenate the lists of multiple getfileinfo runs into a single file.

3. Run normalizefileinfo.py - Build an extension dictionary with all observed Magic Descriptions (and their reference counts) normally extensions.py 

4. Unless the filesystems scanned are 100% correct, you will need to alter the extension dictionary to eliminiate bad "extension -> Magic Description" associations. In some cases a file may have multiple correct entries (ex: a bash shell script on disk may have a .bash instance in one case, but a .sh instance in another). I found that http://www.cleancss.com/python-beautify/ and http://pep8online.com was helpful in locating the enevitable errors in Python syntax come after manual editing.

5. Move this dictionary file to dicts/extension.dict

6. The dictionary above contains a "suffix -> Magic Description" but for all pracical puposes, the entry point for logic will be based on the Magic Desciption. createrevfileinfo.py file reverses this map (flipping the relationship in extensions.dict from suffix -> Magic Description to Magic Description -> suffix). createrevfileinfo.py then overlays some additional "file dispensation" data in the defaultext.dict -- namely the default suffix reccomended be used for the type of file (a DEFAULT key), and a never suggest or rewrite files of this type with a specific suffix (an EXCLUDE key). createrevfileinfo.py requires two main files to build out the final dictionary -- extensions.dict and default.dict -- and produces a final revextension.dict file. 

7. The construction of extensions.dict is described above. The inital defaultext.dict file can be created by running createrevfilefinfo on the current extensions file, but this generates a defaultext.dict file that may be to active it what it tries to do. Manually ditng this file is reccomended. 
7a. Remove any entries that you never want to move/modify.
7b. Validate that the DEFAULT entry (an array of a single suffix) for the remaining entries is the one you wish to use. The DEFAULT entry (optional) is used when suggesting or executing a suffix change when there may be mutiple valid, possible suffixes on disk (ex: jpe, jpg, jpeg).
7c. Add EXCLUDE entries (entry) for extensions that also should be exempt from final reporting/moving/modification. The EXCLUDE entry is used when the Magic Description may overlap with files that share a common Magic Description (exmaple, a JPEG stero file still has a JPEG header, but will still want the jps suffix unaltered).
7d. You can always edit/review the extensions.dict and/or the temporary revextensions.dict while editing the defaultext file as the different representations of the Magic <-> suffix relationships may require some massaging. 
8. Move this defaultext.dict file into ./dicts/defaultext.dict

9. Run createrevfileinfo against the extensions.dict and the defaultext.dict file in the ./dicts folder. If you told the script to output the resulting revextensions.dict file to some other location that the ./dicts folder, please move it there now.


The execution of createrevfileinfo.py + the extension.dict + the defaultext.dict file will result in the revextension.dict file which will be used for any future processing by validatefileinfo.py.

validatefileinfo.py
 -h help
 -d debug
 -e extdict (default override)
 -m report, move, or rename
 -l logfile (will also include debug entries if -d is used)
 -C case: upper, lower (default)
 -r report filename
 -s subdirectory (assuming relative to the files location unless an absolute path is given)



Other files and directories:

dicts - Directories of python dictionaries common to various scripts.
README.md - This document
magicfixup.py - A subroutine to regex around some poorly formatted Magic Descriptions
