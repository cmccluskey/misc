# vim: set fileencoding=utf-8
import re

# Regex our way out of some magic verboseness 
def magicfixup(olddesc,debug):

# Split out after the comma to remoce extended data
	fixedup = olddesc.split(',')[0]

#(notice extra leading space before hyphen)
	fixedup = fixedup.split('  - ')[0]

#Split on ‘ - ‘
	fixedup = fixedup.split('  - ')[0]

#'SysEx File -': 5
	regex = r'(.*)%s$' % re.escape(' -')
        fixedup = re.sub(regex, r'\1', fixedup)

#Filter out anything after ‘ data’
#"ISO 9660 CD-ROM filesystem data 'warimg' (bootable)": 1,
#"UDF filesystem data (version 1.5) 'DESKTOP'": 1,
#'PCX ver. 2.5 image data bounding box [33': 1,
#'PCX ver. 2.5 image data bounding box [3514': 1,
#'PCX ver. 2.5 image data bounding box [7371': 1,
#'PCX ver. 2.8 image data': 1,
#'PCX ver. 3.0 image data bounding box [22479': 1,
#"Macintosh HFS Extended version 20047 data (mounted) (spared blocks) (unclean) last mounted by: ',
#'TeX generic font data': 1,
	regex = r'(.* data).*$'
	fixedup = re.sub(regex, r'\1', fixedup)

#"# ISO 9660 CD-ROM filesystem data ‘isoname’”: 1},
#"# UDF filesystem data (version 1.5) 'JESSIE_R__PEREA'": 1,
#"# UDF filesystem data (version 1.5) 'UNTITLED_PROJECT'": 1},
	regex = r'^%s(.*)' % re.escape('# ') 
	fixedup = re.sub(regex, '', fixedup)

#'mp3': {   'Audio file with ID3 version 2.2.0': 139,
#‘Audio file with ID3 version 2.2.0': 3195,
	if re.match('^Audio file with ID3', fixedup):
		fixedup = 'Audio file with ID3'
	else: None

#'Compiled PSI (v2) data (XXX)': 1,
	regex = r'^%s' % re.escape('Compiled PSI (v2) data')        
	if re.match(regex, fixedup):
		fixedup = 'Compiled PSI (v2) data'
	else: None

#'mlterm': {   'Compiled terminfo entry "screen.mlterm"': 1},
	regex = r'^%s' % re.escape('Compiled terminfo entry')
	if re.match(regex, fixedup):
		fixedup = 'Compiled terminfo entry'
	else: None

#'eps': {   'DOS EPS Binary File Postscript starts at byte 30 length 125527 TIFF starts at byte 125557 length 5044': 1,
	regex = r'^%s' % re.escape('DOS EPS Binary File')
	if re.match(regex, fixedup):
		fixedup = 'DOS EPS Binary File'
	else: None

#'Dyalog APL version 10 .35': 1,
#'Dyalog APL version 105 .199': 1,
#'Dyalog APL version 107 .69': 1,
	regex = r'^%s' % re.escape('Dyalog APL')
	if re.match(regex, fixedup):
		fixedup = 'Dyalog APL'
	else: None

#'Mach-O universal binary with 2 architectures: [i386: Mach-O i386 dynamically linked shared library': 1},  -> ‘Mach-O universal binary’
	regex = r'^%s' % re.escape('Mach-O universal binary')
	if re.match(regex, fixedup):
		fixedup = 'Mach-O universal binary'
	else: None

#'multipart/mixed; boundary="AAA"': 3,
	regex = r'^%s' % re.escape('multipart/mixed;')
	if re.match(regex, fixedup):
		fixedup = 'multipart/mixed'
	else: None

#'pfa': {   'PostScript Type 1 font text': 2,
#           'PostScript Type 1 font text (Courier 001.003)': 1,
	regex = r'^%s' % re.escape('PostScript Type 1 font text')
	if re.match(regex, fixedup):
		fixedup = 'PostScript Type 1 font text'
	else: None

#'ps': {   'ASCII text': 7,
#              'PostScript document text': 2,
#              'PostScript document text conforming DSC level 2.0': 16,
	regex = r'^%s' % re.escape('PostScript document text')
	if re.match(regex, fixedup):
		fixedup = 'PostScript document text'
	else: None

#"QDOS object 'XXX'": 2,
	regex = r'^%s' % re.escape('QDOS object')
	if re.match(regex, fixedup):
		fixedup = 'QDOS object'
	else: None

#'TeX DVI file (XXX)': 1,
	regex = r'^%s' % re.escape('TeX DVI file')
	if re.match(regex, fixedup):
		fixedup = 'TeX DVI file'
	else: None

	if debug: print "Info: Was: %s\nInfo: Now: %s\n" % (olddesc,fixedup) 

	return fixedup
