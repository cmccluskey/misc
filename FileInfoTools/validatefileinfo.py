#!/usr/bin/python3
# brew install libmagic
# via pip install python-magic
import argparse
import magic
import os
import re
import stat
import sys
from datetime import datetime
from magicfixup import magicfixup

# Counters
countTotal      = 0 # Scanned plus all no-scan cases
countScanned    = 0 # Scanned cases total (see below)
#countNoAccess   = 0 # Unscanned
noAccess        = []
countSkipped    = 0 # Unscanned
#countExcluded   = 0 # Unscanned
#countSymLink    = 0 # No real file
symlink         = []
socket          = []

# Counters of scanned items
countCorrect    = 0 # All is good
countCase       = 0 # Extension case was messed up
countVariant    = 0 # Proper variant of extension
#countIncorrect  = 0 # Invalid extension noted
incorrect       = []
#countMissingExt = 0 # No extension
missingExt      = []
#countMissingDesc= 0 # No description entry
missingDesc     = [] 

# Timers
startTime       = datetime.now()
endTime         = 0

## Temporary file extension
#temp_ext        = ".tmp"

# Move to commmon
def build_file_tree(items=[], recurse=False):
  norecursedirs = ['__Trash']
  temp_dict = {}
  for item in args.items:
    if os.path.isfile(item):
      temp_dict[os.path.abspath(item)] = item 
    if item == '*':
      item = os.getcwd()
    if os.path.isdir(item):
      if recurse:
        found = False
        for norecursedir in norecursedirs:
          if norecursedir in item:
            found = True
        if not found: 
          for root, dirs, files in os.walk(item):
            for f in files:
              temp_dict[os.path.abspath(os.path.join(root,f))] = item
      else:
        for possiblefile in os.listdir(item):
          if os.path.isfile(os.path.join(item, possiblefile)):
            temp_dict[os.path.abspath(os.path.join(item, possiblefile))] = item
  return sorted(temp_dict.keys())


# Move to commmon
def delete_file(filename, trash_folder = None, actionfile = None, logger = None, fatal_error = True):
  if logger:
    logger.debug("In delete_file")
  if os.path.isfile(filename): 
    if trash_folder:
      basedir = os.path.dirname(filename)
      trash_folder_pathed = os.path.join(basedir, trash_folder)
      if os.path.isdir(trash_folder_pathed):
        if not os.access(trash_folder_pathed, os.W_OK):
          if logger:
            logger.error("Cannot write to trash folder %s" % trash_folder_pathed)
          else:
            print("Error: Cannot write to trash folder %s" % trash_folder_pathed)
          if fatal_error:
            sys.exit(1)
      else:
        try:
          os.makedirs(trash_folder_pathed, exist_ok=True)
        except OSError as exc: 
          if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
          else:
            if logger:
              logger.error("Cannot create trash folder %s" % trash_folder_pathed)
            else:
              print("Error: Cannot create trash folder %s" % trash_folder_pathed)
            if fatal_error: 
              sys.exit(1)
        # Action statement
        if actionfile:
          actionfile.write("\n")
          actionfile.write("Date: %s\n" % str(time.time()) )
          actionfile.write("Action: CreateDir\n")
          actionfile.write("Object: %s\n" % trash_folder_pathed)
      existing_file = os.path.join(trash_folder_pathed, os.path.basename(filename))
      if os.path.isfile(existing_file):
        if logger:
          logger.error("Would overwrite exsiting file in Trash folder. Please remove content in Trash folder.")
        else:
          print("Error: Would overwrite exsiting file in Trash folder. Please remove content in Trash folder.")
        if fatal_error: 
          sys.exit(1)
      try:
        shutil.move(filename,trash_folder_pathed)
      except:
        if logger:
          logger.error("Cannot move file %s to trash folder %s" % (filename, trash_folder_pathed))
        else:
          print("Error: Cannot move file %s to trash folder %s" % (filename, trash_folder_pathed))
        if fatal_error: 
          sys.exit(1)
      if actionfile:
        actionfile.write("\n")
        actionfile.write("Date: %s\n" % str(time.time()) )
        actionfile.write("Action: MoveFile\n")
        actionfile.write("Object: %s\n" % filename)
        actionfile.write("Destination: %s\n" % existing_file)
    else:
      try:
        os.remove(filename)
      except:
        if logger:
          logger.error("Cannot remove file %s" % filename) 
        else:
          print("Error: Cannot remove file %s" % filename)
        if fatal_error: 
          sys.exit(1)
      if actionfile:
        actionfile.write("\n")
        actionfile.write("Date: %s\n" % str(time.time()) )
        actionfile.write("Action: DeleteFile\n")
        actionfile.write("Object: %s\n" % filename)
  else:
    if logger:
      logger.error("File %s went away before we could delete" % filename)
    else:
      print("Error: File %s went away before we could delete" % filename)
    if fatal_error: 
      sys.exit(1)
       
# Move to commmon
def move_file(fromfile, tofile, actionfile = None, logger = None, fatal_error=True):
  if logger:
    logger.debug("In move_file")
  if os.path.isfile(tofile):
    if logger:
      logger.error("Move of %s would overwrite existing file %s." % (fromfile, tofile))
    else:
      print("Error: Move of %s would overwrite existing file %s." % (fromfile, tofile))
    if fatal_error: 
      sys.exit(1)
  else:
    try:
      shutil.move(fromfile,tofile)
    except Exception as e:
      print(str(e))
      if logger:
        logger.error("Cannot move file %s to file %s" % (fromfile, tofile)) 
      else:
        print("Error: Cannot move file %s to file %s" % (fromfile, tofile))
      if fatal_error: 
        sys.exit(1)
    if actionfile:
      actionfile.write("\n")
      actionfile.write("Date: %s\n" % str(time.time()) )
      actionfile.write("Action: MoveFile\n")
      actionfile.write("Object: %s\n" % fromfile)
      actionfile.write("Destination: %s\n" % tofile)


# Ok to process based on exclude list
def excludeRootCheckPassed(checkfile, myList):
  checkfile = os.path.dirname(checkfile)
  for x in myList:
    regex = '^' + re.escape(x)
    if re.search(regex,checkfile):
      return False
    else: None
  return True


def excludeDirCheckPassed(checkfile, myList):
  checkfile = os.path.dirname(checkfile)
  for x in myList:
    regex = re.escape(x)
    if re.search(regex,checkfile):
      return False
    else: None
  return True


def changeCase(filename, extension, case, extdict):
  (path, strippedfile, strippedext) = fileParts(filename)
  if ( case == 'lower'):
    strippedext = strippedext.lower()
  elif (case == 'upper'):
    strippedext = strippedext.upper()
  elif (case == 'stored'):
    if (extdict['DEFAULT'][0]):
      strippedext = extdict['DEFAULT'][0]
    else:
      strippedext = extension
  else: None
  returnfile = path + '/' + strippedfile + '.' + strippedext
  if (args.debug): print("changeCase: returnfile: %s" % returnfile)
  return (returnfile)


def changeExt(filename, extension, case, extdict = {}):
  (path, strippedfile, strippedext) = fileParts(filename)
  filename = path + '/' + strippedfile + '.' + extension
  if (args.debug): print("changeExt: filename: %s" % filename)
  return filename


def changeMovePath(filename, path):
  movedir_clean = path.rstrip('/')
  (tpath, tfile, textension) = fileParts(filename)
  if not excludeRootCheckPassed(movedir_clean, ['/']):
    movedir_clean = os.path.abspath(movedir_clean)
    if (args.debug): print("Absolute move path found.")
    if textension:
      return movedir_clean + '/' + tfile + '.' + textension
    else:
      return movedir_clean + '/' + tfile
  else:
    movedir_clean = os.path.basename(movedir_clean)
    if (args.debug): print("Relative move path found.")
    if textension:
      return tpath + '/' + movedir_clean + '/' + tfile + '.' + textension
    else:
      return tpath + '/' + movedir_clean + '/' + tfile 


def writeLog(handles, line, newline=True):
  for handle in handles:
    handle.write(line)
    if newline:
      handle.write('\n')
  return True


def fileParts(filename):
  (path, fileproper) = os.path.split(filename)
  if '.' in fileproper:
    (base, extension) = fileproper.rsplit('.',1)
  else:
    base = fileproper
    extension = ''
  if (args.debug): print("fileParts: %s %s %s" % (path, base, extension))
  return [path, base, extension]


# Parser setup
parser = argparse.ArgumentParser(description='Validate files extensions based on Magic description. Either report, rewrite, or move files that do not conform to the dictionary.')

parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Enable debugging to standard out')
parser.add_argument('-e', dest='revextdict', default='./dicts/revextension.dict', help='Override the location of the extension dictionary') 
parser.add_argument('-C', dest='case', default='lower', nargs=1, choices=['upper','lower','asis'], help='Specify case (default lower).')
parser.add_argument('-A', dest='addext', action='store_true', default=False, help='Add an extension if a default extension is available. If in report mode, log if DEFAULT is not found.')
parser.add_argument('-D', dest='forcedefext', action='store_true', default=False, help='Force the use of the default extension, even if the current extension is valid.') 
parser.add_argument('-S', dest='summary', action='store_true', default=False, help='Display the stats summary at the end of the run. If a report is requested, the stats will be written to the end of the report.') 
parser.add_argument('-r', dest='reportfile', default=False, help='Same as testonly, store the report at this location.')
parser.add_argument('-t', dest='testonly', default=False, help='Do not perform any modification to files, but print what would have been done.')
parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='Normally skipped, unavailable, and ok files are not written to the report, this enables those entries in the report.') 
parser.add_argument('-c', dest='caserun', action='store_true', default=None, help='Change the case only after validation.')
parser.add_argument('-m', dest='moverun', default=None, help='Move the file if it does not match the dictionary. Specify a subdirectory relative to the current filename in which to move the file, or a full path to move to a fixed location.')
parser.add_argument('-n', dest='renamerun', action='store_true', default=None, help='Perform a rename run, modifying the suffix.')
parser.add_argument('-R', dest='recurse', action='store_true', default=False, help='Recurse into directories.')
parser.add_argument('-nlog', dest='actionlog', action='store_const', const=None, default='action.log', help='Disable action log generation.')
parser.add_argument('-ntrash', dest='trash', action='store_const', const=None, default='__Trash',  help='Disable use of Trash folder.')
parser.add_argument('-nfatal', dest='fatal', action='store_const', const=False, default=True,  help='Make file errors a non-fatal issue (not-recomended).')
parser.add_argument('items', nargs='+', default=None)

args = parser.parse_args()


## Enable logger
#logging.basicConfig()
#logger = logging.getLogger(__name__)
#if (args.debug):
#   logger.setLevel(logging.DEBUG)
#else:
#   logger.setLevel(logging.ERROR)
##for lh in (""):
##   logging.getLogger(lh).setLevel(100)

# Make sure one of the primary validation modes is set
if not (args.caserun or args.moverun or args.renamerun):
  parser.print_help()
  print("Error: One of the runtime modes must be to run a report (-r), change the case (-c), move nonconforming files to a directory (-m), to rename in place (-n).")
  sys.exit(1)

# Make sure that there isn't more than one validation mode set
#if ( (args.caserun and args.moverun and args.renamerun) or 
#     (args.caserun and args.renamerun) or (args.caserun and args.moverun) or 
#     (args.moverun and args.renamerun) ):
#  parser.print_help()
#  print("Error: The runtime mode must be only one of changing the case (-c), move nonconforming files to a directory (-m), to rename in place (-n).")
#  sys.exit(1)

# Make sure we have a report file name
if args.reportfile:
  if not isinstance(args.reportfile, str):
    parser.print_help()
    print("Error: A report was requested but a filename wasn't provided.")
    sys.exit(1)

## Don't navigate these root paths
## TODO: Add as argument or config file
#exclude_paths = ['/dev','/tmp','/Volumes']
#
## Don't navigate paths containing the following strings (useful if you have long lived directories from the rumtime mode move)
## TODO: Add as argument or config file
##exclude_directories = ['_bad','_badsuffix']
#exclude_directories = ['_badXXXXxxxxx']

## Validate and add movedir to the proper exclude bucket
#if args.moverun:
#  movedir_clean = args.moverun.rstrip('/')
#  if not excludeRootCheckPassed(args.moverun, ['/']):
#    movedir_clean = os.path.abspath(movedir_clean)
#    exclude_paths.append(movedir_clean)
#  else:
#    movedir_clean = os.path.basename(movedir_clean)
#    exclude_directories.append(movedir_clean)
#else: None

# Open report file
if args.reportfile:
  try:
    outf = open(os.path.abspath(args.reportfile), 'w')
  except IOError:
    print("Error: Cannot open reportfile %s for writing." % args.reportfile)
    sys.exit(1)

# Setup active logging handles
active_log_handles = []
if args.reportfile:
  active_log_handles.append(outf)
if args.debug or args.testonly:
  active_log_handles.append(sys.stdout)
if args.debug:
  writeLog(active_log_handles, "Debug: %s" % args) 

# Attempt to load the revextension dict
try:
  inf = open(os.path.abspath(args.revextdict), 'r')
except IOError:
  writeLog(active_log_handles, "Error: Cannot load revextension dict from %s." % os.path.abspath(args.revextdict))
  sys.exit(1)
else:
  exec(inf)
  if (len(revextension.keys()) < 2):
    writeLog(active_log_handles, "Error: Cannot load dict %s. Not enough records loaded (%s)." % (revextdict,len(revextension.keys())))
    sys.exit(1)
  else:
    if args.debug:
      writeLog(active_log_handles, "Info: %s keys loaded into revextension dict." % (len(revextension.keys())))
  inf.close()

# Build file list via path recursion
files = build_file_tree(args.items, args.recurse)

# Walk the tree and write out line
for testfile in files:
  countTotal += 1
  if (args.debug): print("Processing %s ..." % testfile)
  # Placeholder for changes
  modifiedfile = ''
  # Flag for case rewrite
  casechange = False
  # Flag for modification
  modifychange = False
  # Flag for move
  movechange = False
  # Suffix to use
  extensionchange = ''
#  # Check for excluded paths from root
#  if excludeRootCheckPassed(testfile,exclude_paths):
#  # Check excluded directories
#  if excludeDirCheckPassed(testfile,exclude_directories): 
  # Check for a symlink which messes with the socket check
  if os.path.islink(testfile):
    countSkipped +=1
    symlink.append(testfile)
    if (args.verbose): 
      writeLog(active_log_handles, "%s skipped as a symlink." % (testfile))
    elif (args.debug): 
      print("%s skipped as a symlink." % (testfile))
    break
  else:
    # Readable as the current user
    try:
      fp = open(testfile,'r')
    except IOError:
      countNoAccess +=1
      noAccess.append(testfile)
      if (args.verbose): 
        writeLog(active_log_handles, "%s skipped due to access permissions." % (testfile))
      elif (args.debug): 
        print("%s skipped due to access permissions." % (testfile))
      break
    else:
      if fp: fp.close()
      # Checking to see if file is a socket
      mode = os.stat(testfile).st_mode
      if stat.S_ISSOCK(mode):
        countSkipped += 1
        socket.append(testfile)
        if (args.verbose): 
          writeLog(active_log_handles, "%s skipped as a named socket/pipe." % (testfile))
        elif (args.debug): 
          print("%s skipped as a named socket/pipe." % (testfile))
        break
      else:
        # We are going to Scan this file now
        countScanned += 1
  # Finally, let's scan this file
  if (args.debug): print("Testfile: %s" % testfile)
  extension = fileParts(testfile)[2]
  if (args.debug): print("Extension: %s" % extension)
  description = magicfixup(magic.from_file(testfile), False)
  if (description in revextension.keys()):
    # Confirm there is an extension on the file
    if extension:
      # Note a case fault. If we aren't rewriting case, revert the "destination" file back to the original.
      # Future case changes will be done on extension rewrites.      
      tryfile = changeCase(testfile, extension, args.case, revextension[description])
      if not (tryfile == testfile):
        countCase += 1
        if args.caserun:
          writeLog(active_log_handles, "%s has bad case (%s) and will be changed to %s." % (testfile,args.case,casefile))
          casechange = True                      
        else: None 
      else: None
      # Check extension via description
      if ('DEFAULT' in revextension[description].keys()):
        if (extension.lower() == revextension[description]['DEFAULT'][0].lower()):
          # Yes, the extension is correct for the description 
          if (args.verbose): writeLog(active_log_handles, "%s has the correct extension '%s' for '%s'." % (testfile,extension,description))
          elif (args.debug): print("%s has the correct extension '%s' for '%s'." % (testfile,extension,description))
          countCorrect += 1
        else:
          if ('EXCLUDE' in revextension[description].keys()):
            if extension.lower() in revextension[description]['EXCLUDE']:
              if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description))
              elif (args.debug): print("%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description))
              countVariant += 1
            else:
              writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
              countIncorrect += 1
              modifychange = True
              movechange = True
              extensionchange = revextension[description]['DEFAULT'][0]
          else:
            writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
            countIncorrect += 1
            modifychange = True
            movechange = True
            extensionchange = revextension[description]['DEFAULT'][0]
      # Is a variant
      elif (extension.lower() in revextension[description].keys()):
        # Is this extension EXCLUDED from being rewritten
        if ('EXCLUDE' in revextension[description].keys()):
          if extension.lower() in revextension[description]['EXCLUDE']:
            # In the exclude list, so don't change the file
            if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description))
            elif (args.debug): print("%s has a known extension '%s' for '%s' but is excluded from changes." % (testfile,extension,description))
          else: None
          countVariant += 1
        else:
          # Is there a DEFAULT?
          if ('DEFAULT' in revextension[description].keys()):
            if args.forcedefext:
              writeLog(active_log_handles, "%s has a known extension '%s' for '%s' but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
              modifychange = True
              movechange = True
              extensionchange = revextension[description]['DEFAULT'][0]
              countVariant += 1
            else:
              if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s'." % (testfile,extension,description))
              elif (args.debug): print("%s has a known extension '%s' for '%s'." % (testfile,extension,description))
              countVariant += 1  
          else:
          # There isn't a default, so do nothing
            if (args.verbose): writeLog(active_log_handles, "%s has a known extension '%s' for '%s' and the extension won't be changed." % (testfile,extension,description))
            elif (args.debug): print("%s has a known extension '%s' for '%s' and the extension won't be changed." % (testfile,extension,description))
            countVariant += 1
      else:
        # Assuming incorrect extension for description
        countIncorrect += 1
        # Is there an alternate extenstion available?
        if ('DEFAULT' in revextension[description].keys()):
          if args.forcedefext:
            writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but will be changed to the default '%s'." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
            modifychange = True
            movechange = True
            extensionchage = revextension[description]['DEFAULT'][0]
          else: 
            writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but the default extension '%s' will not be assigned." % (testfile,extension,description,revextension[description]['DEFAULT'][0]))
            movechange = True
        else:  
          writeLog(active_log_handles, "%s has an incorrect extension '%s' for description '%s', but it's unclear what possible extension to use '%s'." % (testfile,extension,description,revextension[description].keys()))
          movechange = True
    else:
      countMissingExt += 1
      if args.addext:
        if ('DEFAULT' in revextension[description].keys()):
          if (args.addext):
            writeLog(active_log_handles, "%s has no extension, but has a default of '%s' for '%s'." % (testfile,revextension[description]['DEFAULT'][0],description))
            modifychange = True
            extensionchange = revextension[description]['DEFAULT'][0]
          else:
            if (args.verbose): writeLog(active_log_handles, "%s has no extension for '%s', and the default will not be applied." % (testfile,description))
            elif (args.debug): print("%s has no extension for '%s', and the default will not be applied." % (testfile,description))    
        else:
          if (args.verbose): writeLog(active_log_handles, "%s has no extension for '%s', and no default is available." % (testfile,description))
          elif (args.debug): print("%s has no extension for '%s', and no default is available." % (testfile,description))
          movechange = True
      else:
        if (args.verbose): writeLog(active_log_handles, "%s has no extension for '%s', and no default is available." % (testfile,description))
        elif (args.debug): print("%s has no extension for '%s', and no default is available." % (testfile,description))
        movechage = True
    # Now perform the run modes
    if not modifiedfile: 
      modifiedfile = testfile
    if args.verbose: writeLog(active_log_handles, "args.renamerun: %s args.caserun: %s args.moverun: %s modifychange: %s casechange: %s movechange: %s" % (args.renamerun, args.caserun, args.moverun, modifychange, casechange, movechange))
    elif args.debug: print("args.renamerun: %s args.caserun: %s args.moverun: %s modifychange: %s casechange: %s movechange: %s" % (args.renamerun, args.caserun, args.moverun, modifychange, casechange, movechange))
    # Move/rename the file to modfied file name 
    if args.renamerun:
      if modifychange:
        modifiedfile = changeExt(modifiedfile, extensionchange, args.case, revextension[description])
    # Just alter the case of the extension
    if args.caserun:
      if casechange:
        modifiedfile = changeCase(modifiedfile, fileParts(modifiedfile)[2], args.case, revextension[description]) 
    # Change the path of the errored file to a global path OR to local (realtive to file) subdirectory
    if args.moverun:
      if args.verbose: writeLog(active_log_handles, "Debug: In moverun case...")
      elif args.debug: print("Debug: In moverun case...")
      if movechange:
        if (args.verbose): writeLog(active_log_handles, "Debug: Perform movechange modifcation.")
        elif (args.debug): print("Debug: Perform movechange modifcation.")
        modifiedfile = changeMovePath(modifiedfile, args.moverun)
    if (args.renamerun or args.caserun or args.moverun):
      if (args.verbose): 
        writeLog(active_log_handles, "Comparing '%s' and '%s'." % (testfile,modifiedfile))
      elif (args.debug): 
        print("Comparing '%s' and '%s'." % (testfile,modifiedfile))
      if (testfile != modifiedfile):
        # Make sure the directory exists, if not create it
        if not os.path.exists(fileParts(modifiedfile)[0]):
          try:
            os.makedirs(fileParts(modifiedfile)[0])
          except OSError:
            writeLog(active_log_handles, "Error: Cannot create directory %s." % (fileParts(modifiedfile)[0]))
            sys.exit(1)
          else:
            # Make sure the destination doesn't exit, else throw error and bail for now
            None
        if not os.path.isfile(modifiedfile):
          writeLog(active_log_handles, "Moving %s to %s... " % (testfile,modifiedfile))
          move_file(testfile,modifiedfile)
#          try:
#            move_file(testfile,modifiedfile)
#            os.rename(testfile,modifiedfile)
#          #  None
#          except OSError:
#            writeLog(active_log_handles, "FAILED")
#            writeLog(active_log_handles, "Cannot move %s to %s." % (testfile,modifiedfile))
#            sys.exit(1)
#        else:
          writeLog(active_log_handles, "OK")  
        else:
          writeLog(active_log_handles, "Error: Won't clobber existing file %s." % (modifiedfile))
          sys.exit(1) 
      else:
        if (modifychange or casechange or movechange):
          if (args.verbose):
            writeLog(active_log_handles, "File %s has no changes." % (testfile))
          elif (args.debug): 
            print("File %s has no changes." % (testfile))
          else: None
#            print("Error: There is no difference in the source file %s or its destination. This shouldn't happen!" % testfile)
#            sys.exit(1)
        else:
          if (args.verbose):
            writeLog(active_log_handles, "File %s has no changes." % (testfile))
          elif (args.debug): print("File %s has no changes." % (testfile))
          else: None
    else:
      if (args.verbose): writeLog(active_log_handles, "No modification of %s required." % (testfile))
      elif (args.debug): print("No modification of %s required." % (testfile))
  else:
    # There is no description found in revextensions
    countMissingDesc += 1
    if (args.verbose): writeLog(active_log_handles, "%s doesn't have a valid description '%s' in the revextension dict." % (testfile,description))
    elif (args.debug): print("%s doesn't have a valid description '%s' in the revextension dict." % (testfile,description))


# Do stats calculation
endTime         = datetime.now()
elapsed      = (endTime - startTime).total_seconds()
#print elapsed
filePerSec    = 0.0
filesPerSec    = countTotal / elapsed

# Open report file for header placement
if args.reportfile:
  try:
    reportf = open(os.path.abspath(args.reportfile), 'w')
  except IOError:
    print("Error: Cannot open reportfile %s for writing." % (args.reportfile))
    sys.exit(1)
  else: None
else: None

if args.reportfile:
  reportf.write("\n")
  reportf.write("Report for files in path: %s\n" % (args.path) )
  reportf.write("\n")
  reportf.write("Report start time: %s\n" % (startTime) )
  reportf.write("Report end time:   %s\n" % (endTime) )
  reportf.write("%s files were processed in total, at a rate of %.2f files per second.\n" % (countTotal, filesPerSec))
  reportf.write("\n")
  reportf.write("%s%s%s Total Count\n" % (str(countTotal).ljust(10), ''.ljust(10), ''.ljust(10)))
  reportf.write("%s%s%s No Access\n" % (''.ljust(10), str(countNoAccess).ljust(10), ''.ljust(10)))
  reportf.write("%s%s%s Skipped\n" % (''.ljust(10), str(countSkipped).ljust(10), ''.ljust(10)))
  reportf.write("%s%s%s Excluded\n" % (''.ljust(10), str(countExcluded).ljust(10), ''.ljust(10)))
  reportf.write("%s%s%s Symlink\n" % (''.ljust(10), str(countSymLink).ljust(10), ''.ljust(10)))
  reportf.write("%s%s%s Scanned\n" % (''.ljust(10), str(countScanned).ljust(10), ''.ljust(10)))
  reportf.write("%s%s%s Correct\n" % (''.ljust(10), ''.ljust(10), str(countCorrect).ljust(10)))
  reportf.write("%s%s%s Acceptable Variant in Extension\n" % (''.ljust(10), ''.ljust(10), str(countVariant).ljust(10)))
  reportf.write("%s%s%s Incorrect Extension\n" % (''.ljust(10), ''.ljust(10), str(countIncorrect).ljust(10)))
  reportf.write("%s%s%s Missing Extension\n" % (''.ljust(10), ''.ljust(10), str(countMissingExt).ljust(10)))
  reportf.write("%s%s%s Missing Description\n" % (''.ljust(10), ''.ljust(10), str(countMissingDesc).ljust(10)))
  reportf.write("%s%s%s Incorrect Case (not included in Scanned Count)\n" % (''.ljust(10), ''.ljust(10), str(countCase).ljust(10)))
  reportf.write("\n\n")
  reportf.write("Data\n")
  reportf.write("__________________________________________\n")
  while True:
    line = tempf.readline()
    if line == '':
      break
    else:
      reportf.write(line)
  reportf.close()
  tempf.close()
else: None

## Delete temp file
#os.remove(os.path.abspath(args.reportfile + temp_ext))
