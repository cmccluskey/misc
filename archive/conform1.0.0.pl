#!/usr/bin/perl -w 
########################################################################
#
#	conform -- Rewrites filenames to a more precise standard
#
########################################################################
# Release Notes: 
# 1.0.0		Developed on Windows platform. Not fully tested on *ix  
#
#
#
#
#
#
#
#
#
########################################################################
$MAJOR = 1;
$MINOR = 0;
$REVISION = 0;
$VERSION = "$MAJOR.$MINOR.$REVISION";
# Command and Interface Variables
$DEBUG = 0;
$VERBOSE_FLAG = 0;
$DBL_VERBOSE_FLAG = 0;
$INTERACT_FLAG = 0;	# Ask before delete?
$DBL_INTERACT_FLAG = 0;	# Ask before remove and delete?
$FILE_SAFE = 0;		# For testing purposes -- won't write changes to disk
$NOTUNIX = 1;		# For use with non UNIX systems like Windows
			# Expands '*' and '*.*' command line options
$DIRSEP = "/";		# Directory symbol: Windows (\), UNIX (/), Mac (:)
########################################################################
# Rewrite Conditions
$NO_DUP_SPECIAL = 1;		# Do not allow duplacte special chars (eg. ++)
$SQUASH_FILTER = 1;		# General filter fileFilterString.extn -> file.extn 
				# Strings to delete (case insensitive) 
@FILTER_STRINGS = ('copy of ', ' copy', 'Copy \(\d*\) of '); 
$SQUASH_DOUBLE_DOT = 1;		# file.name.extn -> file?name.extn
$SQUASH_DOUBLE_EXTN = 1;	# filename.extn.extn -> filename.extn
$LOWER_EXTN = 1;		# filename.EXTN -> filename.extn
$ALL_UPPER = 0; 		# FileName.ExTn -> FILENAME.EXTN 
				# Overrides LOWERCASE_EXTN and ALL_LOWERCASE
$ALL_LOWER = 0;			# FileName.ExTn -> filename.extn

				# Lists of extensions to rewrite
				# Before	After
%EXTN_REWRITE = (		"jpeg", 	"jpg", 
				"jpe", 		"jpg", 
				"jpg", 		"jpg", 
				"giff", 	"gif", 
				"gif", 		"gif", 
				"mpeg", 	"mpg", 
				"mp2", 		"mpg", 
				"mpe", 		"mpg",
 				"mpg", 		"mpg", 
				"avi",		"avi",
				"qt", 		"mov", 
				"mov", 		"mov", 
				"tiff", 	"tif", 
				"tif", 		"tif",
				"mp3", 		"mp3",
				"htm",		"html",
				"html",		"html",
				"text",		"txt",
				"txt",		"txt",
				"bmp",		"bmp" );

$CAP_AFTER = 1;			# Captializes the first letter after a special char
$CAP_LEADING = 1;		# Captializes the first letter of the filename
					
$REWRITE_SPECIAL_CHARS = 1;	# Enable the rewriting of special chars (see below)

				# Lists of special chars to rewrite (no: .)
				# Rewrites done in order presented
				# Try not to rewrite SERIAL_SYMBOL so that future serials 
				# can be created for a specific file
				# Do not modify the \ / and : to prevent directory errors
				# SRT 	END
@SPECIAL_REWRITE = (		'+', 	'', 
				'-', 	'-', 
				'&',	' and ',
				'~',	'-', 
				'=', 	'-', 
				'_', 	'_',
				'!s',	'',
				'!', 	'_',
				'rack ','rack',		# Fixes a small issue with the track numbers
				'RACK ','RACK',		# being interpreted as a serial
				'rack-','rack',
				'RACK-','RACK',
				'rack_','rack',
				'RACK_','RACK',
				'quote','-',
				'quot',	'-',
				'nbsp',	'_',
				'%2520','-',
				'%20',	'_',
				'%25',	'-',
				'&', 	'&', 
				'@', 	'_', 
				'^', 	'', 
				':', 	'',
 				'$', 	'', 
				'%', 	'_', 
				'|', 	'_', 
				'#', 	'_',
				';', 	'_', 
				'?', 	'', 
				'*', 	'', 
				'`', 	'', 
				',', 	'',
 				'(', 	'(', 	
				')', 	')', 
				'[', 	'(',	
				']', 	')',
 				'<', 	'(',
				'>', 	')',
 				'{', 	'(',
				'}', 	')',
				'\'', 	'',
				' ', 	'_',
				') ',	')-',
				')_',	')-',
				'_(',	'-(',
				'(_',	'(', 
				'_)',	')',
				'_-', 	'-', 
				'-_', 	'-'	);
				
@CAP_AFTER = (	'(', ')', '{', '}', '[', ']', '<', '>', '-', '_');
			
$SQUASH_PLUS = 1;		# file+name.extn -> filename.extn
$SQUASH_DASH = 0;		# file-name.extn -> filename.extn
$SQUASH_BANG = 1;		# file!name.extn -> filename.extn
$SQUASH_AMP = 1;		# file&name.extn -> filename.extn
$SQUASH_AT = 0;			# file@name.extn -> filename.extn
$SQUASH_BACKSLASH = 1;		# file\name.extn -> filename.extn
$SQUASH_CARAT = 1;		# file^name.extn -> filename.extn
$SQUASH_COLON = 1;		# file:name.extn -> filename.extn
$SQUASH_DOLLAR = 1;		# file$name.extn -> filename.extn
$SQUASH_PERCENT = 1;		# file%name.extn -> filename.extn
$SQUASH_PIPE = 1;		# file|name.extn -> filename.extn
$SQUASH_POUND = 1;		# file#name.extn -> filename.extn
$SQUASH_SEMICOLON = 1;		# file;name.extn -> filename.extn
$SQUASH_QUESTION = 1;		# file?name.extn -> filename.extn
$SQUASH_STAR = 1;		# file*name.extn -> filename.extn
$SQUASH_TICK = 1;		# file`name.extn -> filename.extn
$SQUASH_TILDE = 1;		# file~name.extn -> filename.extn
$SQUASH_COMMA = 1;		# file,name.extn -> filename.extn
$SQUASH_UNDERSCORE = 0;		# file_name.extn -> filename.extn
$SQUASH_EQUAL = 0;		# file=name.extn -> filename.extn
$SQUASH_DBLQUOT = 1;		# "filename".extn - > filename.extn
$SQUASH_QUOT = 1;		# 'filename'.extn - > filename.extn
$SQUASH_PAREN = 0;		# file(name.extn OR file)name.extn -> filename.extn
$SQUASH_CURLY = 0;		# file{name.extn OR file}name.extn -> filename.extn
$SQUASH_SQUARE = 0;		# file[name.extn OR file]name.extn -> filename.extn
$SQUASH_ANGLE = 0;		# file<name.extn OR file>name.extn -> filename.extn

$SQUASH_PRE_EXTN_CHAR = 1; 	# filename.eXextn -> filename.extn
$SQUASH_POST_EXTN_CHAR = 1; 	# filename.extnX -> filename.extn
$SQUASH_PRE_DOT_CHAR = 1; 	# filenameX.extn -> filename.extn
$SQUASH_POST_DOT_CHAR = 1; 	# filename.Xextn -> filename.extn
$SQUASH_LEADING_CHAR = 1;	# Xfilename.extn -> filename.extn
$SQUASH_UNBALANCED_PAIR = 1;	# file(name.extn OR file)nam(e.extn -> filename.extn
$SQUASH_EXTN_PAIR = 1;		# filename.(extn) -> filename.extn
				# This should be left on unless you wish to add an 
				# EXTN_REWRITE rule for each of the pair possibilites
########################################################################
# Global Variables
#$REPLACE_COUNTER = 1;		# Used for duplicate name scheme filename-XX.extn
$NODOT_FLAG = 0;		# There is no . in the filenamefs
$FILENAME = '';			# Current filename being processed
$NEWFILENAME = '';		# Rewritten filename
$FLAGTEST = '';			# Check for command line argument
$REWRITE_TO_CHAR = "_";		# Used to write the serial number for a renamed file
$SERIAL_SYMBOL = "-";		# Used when creating serial numbers filename$SERIAL_SYMBOLnum.extn 
$SERIAL_SYMBOL_CLASS = '[\-\_]';
$SPECIAL_CHAR_CLASS = '[\+\-\~\=\_\!\&\@\\\^\:\$\%\|\#\;\?\*\`\,\'\ ]';
$SPECIAL_PAIR_CLASS = '[\(\)\[\]\<\>\{\}]';
%SPECIAL_PAIRS = (	'(', ')', 
			')', '(', 
			'[', ']', 
			']', '[', 
			'<', '>', 
			'>', '<', 
			'{', '}',
			'}', '{'	);
@SPECIALS = ( 	'+', '-', '~', '=', '_', '!', '&', '@', '^', 
		':', '$', '%', '|', '#', ';', '?', '*', '`', 
		',', '\'', '(', ')', '[', ']', '<', '>', 
		'{', '}'	);
$ALLOW_FOREIGN_EXTN = 0; 	# Keeps EXTNs that don't match a rule
$LEADING_CHAR_INC_PAIRS = 0;	# Includes pairs in SQUASH_LEADING_CHAR
$SERIAL_FOUND = 0;		# Serial found for non-duplicated file to avoid overwriting
				# a file which has the same name as a currently exisiting file
$DELETE_ME_FLAG = 0;		# The renamed file has the same checksum and filename as a 
				# file in the wokring folder, so we delete it
$SAME_FILE = 0;			# A sanity check to make sure that the files are different
########################################################################

if ($NOTUNIX)
{
	use Cwd;			# Used in finding working dir in NON UNIX systems
}

# Number of ARGs applied on command line
$ARGCOUNT = @ARGV;
print "Argcount: $ARGCOUNT\n" if $DEBUG;

while ($FLAGTEST = shift(@ARGV))
{
	if ($FLAGTEST =~ /\A-/)
	{		
		if ($FLAGTEST =~ /-i\b/)
		{
			$INTERACT_FLAG = 1;
			print "INTERACT_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-ii\b/)
		{
			$DBL_INTERACT_FLAG = 1;
			print "DBL_INTERACT_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-d\b/)
		{
			$DEBUG = 1;
			print "DEBUG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-v\b/)
		{
			$VERBOSE_FLAG = 1;
			print "VERBOSE_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-vv\b/)
		{
			$DBL_VERBOSE_FLAG = 1;
			$VERBOSE_FLAG = 1;
			print "VERBOSE_FLAG set\n" if $DEBUG;
			print "DBL_VERBOSE_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-t\b/)
		{
			$FILE_SAFE = 1;
			print "FILE_SAFE set\n" if $DEBUG;
		}
		else
		{
			die("Unsupported argument $FLAGTEST.\n");
		}
	}
	else
	{
		if ($FLAGTEST =~ /\*/)
		{					# Take of OSes that don't parse wildcards on the cmd ln
			if ($NOTUNIX)
			{	
				&ADDFILES(\@FILES,$FLAGTEST);
			}
			else
			{
				die("This is a non UNIX system. A \* was passed as an agument. Please set NONUNIX in the script.\n");
			}
		}
		else
		{
			if (-d $FLAGTEST)
			{
				&ADDFILES(\@FILES,$FLAGTEST);
			}
			else
			{	
				unshift(@FILES,$FLAGTEST);
			}
		}
	}
}

print "Conform -- Filename conformance rename utility, Version $MAJOR.$MINOR.$REVISION\n" if ($DEBUG || $VERBOSE_FLAG || $DBL_VERBOSE_FLAG);

$NO_OF_FILES = @FILES;
if ($DEBUG) { print "Number of files loaded: $NO_OF_FILES\n"; }
if ($NO_OF_FILES < 1)
{
	&USAGE;
}

while (@FILES)
{
#	$REPLACE_COUNTER = 1;	# Index to add to files of the same name with diff cksums
	$NODOT_FLAG = 0;	# Filename contains no dots

	$FILENAME = shift(@FILES); # Get a new file

	if (-f $FILENAME)
	{
		$FILENAME =~ /(.*)$DIRSEP(.*)/;
		$DIRECTORY = $1;
		$NEWFILENAME= $2;
		
		if (defined($DIRECTORY))
		{
			$DIRECTORY = "$DIRECTORY$DIRSEP";
		}
		else
		{
			$DIRECTORY = '';
		}
		
		print "Processing file $NEWFILENAME out of the directory $DIRECTORY...\n" if $DEBUG;

		if ($NEWFILENAME =~/\./) # Does the file have a dot in the name
		{
			if ($NEWFILENAME =~/(.*)\.(.*)\Z/)
			{
				if ($SQUASH_DOUBLE_EXTN) # Check for a double extension
				{
					$NEWFILENAME = &SQUASH_DOUBLE_EXTN($NEWFILENAME);
				}
			}
			if ($NEWFILENAME =~/(.*)\.(.*)\.(.*)/) # Get rid of the extra dots
			{
				if ($SQUASH_DOUBLE_DOT)
				{
					$NEWFILENAME = &SQUASH_DOUBLE_DOT($NEWFILENAME);
				}
			} 
		}
		else
		{
			$NODOT_FLAG = 1;
			print "NODOT_FLAG set\n\n" if $DEBUG;
		}		
		if ($SQUASH_FILTER)
		{
			$NEWFILENAME = &SQUASH_FILTER($NEWFILENAME);
		}
		
		if ($REWRITE_SPECIAL_CHARS)
		{
			$NEWFILENAME = &REWRITE_SPECIAL_CHARS($NEWFILENAME);
		}
		
		if ($ALL_UPPER)					# Case rewrites
		{
			$NEWFILENAME = &ALL_UPPER($NEWFILENAME);
		}
		else
		{
			if ($ALL_LOWER)
			{
				$NEWFILENAME = &ALL_LOWER($NEWFILENAME);
			}
			else
			{
				if ($LOWER_EXTN)
				{
					$NEWFILENAME = &LOWER_EXTN($NEWFILENAME);
				}
			}
		}

		if ($SQUASH_PLUS)
		{
			$NEWFILENAME = &SQUASH_PLUS($NEWFILENAME);
		}

		if ($SQUASH_DASH)
		{
			$NEWFILENAME = &SQUASH_DASH($NEWFILENAME);
		}

		if ($SQUASH_BANG)
		{
			$NEWFILENAME = &SQUASH_BANG($NEWFILENAME);
		}

		if ($SQUASH_AMP)
		{
			$NEWFILENAME = &SQUASH_AMP($NEWFILENAME);
		}

		if ($SQUASH_AT)
		{
			$NEWFILENAME = &SQUASH_AT($NEWFILENAME);
		}

		if ($SQUASH_BACKSLASH)
		{
			$NEWFILENAME = &SQUASH_BACKSLASH($NEWFILENAME);
		}

		if ($SQUASH_CARAT)
		{
			$NEWFILENAME = &SQUASH_CARAT($NEWFILENAME);
		}

		if ($SQUASH_COLON)
		{
			$NEWFILENAME = &SQUASH_BACKSLASH($NEWFILENAME);
		}

		if ($SQUASH_DOLLAR)
		{
			$NEWFILENAME = &SQUASH_DOLLAR($NEWFILENAME);
		}

		if ($SQUASH_PERCENT)
		{
			$NEWFILENAME = &SQUASH_PERCENT($NEWFILENAME);
		}

		if ($SQUASH_PIPE)
		{
			$NEWFILENAME = &SQUASH_PIPE($NEWFILENAME);
		}

		if ($SQUASH_POUND)
		{
			$NEWFILENAME = &SQUASH_POUND($NEWFILENAME);
		}

		if ($SQUASH_SEMICOLON)
		{
			$NEWFILENAME = &SQUASH_SEMICOLON($NEWFILENAME);
		}

		if ($SQUASH_QUESTION)
		{
			$NEWFILENAME = &SQUASH_QUESTION($NEWFILENAME);
		}

		if ($SQUASH_STAR)
		{
			$NEWFILENAME = &SQUASH_STAR($NEWFILENAME);
		}

		if ($SQUASH_TICK)
		{
			$NEWFILENAME = &SQUASH_TICK($NEWFILENAME);
		}

		if ($SQUASH_TILDE)
		{
			$NEWFILENAME = &SQUASH_TILDE($NEWFILENAME);
		}

		if ($SQUASH_COMMA)
		{
			$NEWFILENAME = &SQUASH_COMMA($NEWFILENAME);
		}

		if ($SQUASH_UNDERSCORE)
		{
			$NEWFILENAME = &SQUASH_UNDERSCORE($NEWFILENAME);

		}

		if ($SQUASH_EQUAL)
		{
			$NEWFILENAME = &SQUASH_EQUAL($NEWFILENAME);

		}

		if ($SQUASH_DBLQUOT)
		{
			$NEWFILENAME = &SQUASH_DBLQUOT($NEWFILENAME);

		}

		if ($SQUASH_QUOT)
		{
			$NEWFILENAME = &SQUASH_QUOT($NEWFILENAME);

		}
		if ($SQUASH_PAREN)
		{
			$NEWFILENAME = &SQUASH_PAREN($NEWFILENAME);
		}

		if ($SQUASH_CURLY)
		{
			$NEWFILENAME = &SQUASH_CURLY($NEWFILENAME);
		}
		
		if ($SQUASH_SQUARE)
		{
			$NEWFILENAME = &SQUASH_SQUARE($NEWFILENAME);
		}

		if ($SQUASH_ANGLE)
		{
			$NEWFILENAME = &SQUASH_ANGLE($NEWFILENAME);
		}
		
		# Double check for rewrite -- watch out for loops
		if ($REWRITE_SPECIAL_CHARS)
		{
			$NEWFILENAME = &REWRITE_SPECIAL_CHARS($NEWFILENAME);
		}

		if ($SQUASH_UNBALANCED_PAIR)
		{
			$NEWFILENAME = &SQUASH_UNBALANCED_PAIR($NEWFILENAME);
		}
		
		if ($SQUASH_PRE_DOT_CHAR)
		{
			$NEWFILENAME = &SQUASH_PRE_DOT_CHAR($NEWFILENAME);
		}
		
		
		if ($SQUASH_POST_DOT_CHAR)
		{
			$NEWFILENAME = &SQUASH_POST_DOT_CHAR($NEWFILENAME);
		}

		if ($SQUASH_PRE_EXTN_CHAR)
		{
			$NEWFILENAME = &SQUASH_PRE_EXTN_CHAR($NEWFILENAME);
		}

		if ($SQUASH_POST_EXTN_CHAR)
		{
			$NEWFILENAME = &SQUASH_POST_EXTN_CHAR($NEWFILENAME);
		}

		if ($SQUASH_LEADING_CHAR)
		{
			$NEWFILENAME = &SQUASH_LEADING_CHAR($NEWFILENAME);
		}
		
		if ($SQUASH_EXTN_PAIR)
		{
			$NEWFILENAME = &SQUASH_EXTN_PAIR($NEWFILENAME);
		}
		
		$NEWFILENAME = &EXTN_REWRITE($NEWFILENAME);	# Implicitly rewrite extensions 
		
		if ($NO_DUP_SPECIAL)
		{
			$NEWFILENAME = &SQUASH_DOUBLE($NEWFILENAME);
		}
		
		if ($CAP_AFTER)
		{
			$NEWFILENAME = &CAP_AFTER($NEWFILENAME);
		}
				
		if ($CAP_LEADING)
		{
			$NEWFILENAME = &CAP_LEADING($NEWFILENAME);
		}
		
		#################################################################################
		# Writing changes to disk section. All file name except the serial number 
		# rewrites should be complete now.
		
		$SERIAL_FOUND = 0;
		$DELETE_ME_FLAG = 0;
		$SAME_FILE = 0;
		
		# Check for file duplication and find a proper serial number
		$NEWFILENAME = &GET_SERIAL_NAME($NEWFILENAME);
		
		if ($FILENAME ne $NEWFILENAME)
		{
			if ($DELETE_ME_FLAG)
			{
				&DELETE_FILE($FILENAME,$NEWFILENAME);
			}
			else
			{
				&RENAME_FILE($FILENAME,$NEWFILENAME); 
			}
		}
		else
		{
			if ($DBL_VERBOSE_FLAG)
			{
				print "File $FILENAME filename is unchanged.\n";
			}
		}
	}
	print "\n" if ( $VERBOSE_FLAG || $DBL_VERBOSE_FLAG || $DEBUG || $FILE_SAFE );
} 
print "DONE.\n" if ($DEBUG || $VERBOSE_FLAG || $DBL_VERBOSE_FLAG);

########################################################################
# Subroutines

sub USAGE
{
	print "usage: conform -i -ii -d -v -vv <file list>\n";
	print "\t-i\t Asks confirmation for the deletion of duplicate files (interactive)\n";
	print "\t-ii\t Asks confirmation for the rename and deletion files\n";
	print "\t-d\t Turns debug reporting on\n";
	print "\t-v\t Turns verbose reporting on\n";
	print "\t-t\t Test mode - performs a rewrite, but doesn't modify or delete the files on disk\n";
	print "\nVersion: $MAJOR.$MINOR.$REVISION\n";
	exit;
}

sub ADDFILES
{
	local ($filearr, $directory, $parent_dir);

	$filearr = $_[0];
 	$directory = $_[1];

	$parent_dir = getcwd();
	print "DIR In: $directory, Parent DIR: $parent_dir\n" if $DEBUG;

	$directory =~ s/\*\.\*//;
	$directory =~ s/\*//;
	$directory =~ s/\\/\//g;
	if ($directory eq '')
	{
		$directory = $parent_dir;
		print "Empty DIR found. DIR: $directory\n" if $DEBUG;	
	}
	if (!(-d $directory))
	{
		if ($parent_dir =~ /$DIRSEP\Z/)
		{
			$directory = "$parent_dir$DIRSEP$directory"; 
			print "Trailing $DIRSEP on DIR found. DIR: $directory\n" if $DEBUG;	
		}
		else
		{
			$directory = "$parent_dir$directory"; 
			print "No trailing $DIRSEP on DIR found. DIR: $directory\n" if $DEBUG;	
		}
	}
	print "Opening DIR $directory\n" if $DEBUG;
	opendir(DIR, $directory) || die("Couldn't open directory $directory for reading.\n");
	while ($filename = readdir(DIR))
	{
		$filename = "$directory$DIRSEP$filename";
		$filename =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
		if (-f $filename)
		{
			unshift(@$filearr,$filename);
		}
	}
}

sub CKSUM()
{
	local($checksum,$SUMFILE);
	$SUMFILE = $_[0];
	print "Opening $SUMFILE for checksum\n" if $DEBUG;
	open(FILEIN, $SUMFILE) || die("Couldn't open $SUMFILE for checksum calculation");
	undef $/;
	$checksum = unpack("%32C*",<FILEIN>);
	close(FILEIN);
	return ($checksum);
}

sub SQUASH_DOUBLE_EXTN
{
	local ($in, $out, $temp_start, $temp_end);

	print "SQUASH_DOUBLE_EXTN:\n" if $DEBUG;

	$in = $_[0];
	$in =~ /(.*)\.(.*)\Z/;
	
	$temp_start = $1;
	$temp_end = $2;
	
	while ($temp_start =~ /\Q$temp_end\Z/i) # was temp_dblextn_esc_end
	{
		$temp_start =~ s/\Q$temp_end\Z//;
	}
	$out = "$temp_start.$temp_end";
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_DOUBLE_DOT
{
	local ($in, $out, $temp_start, $temp_end);

	print "SQUASH_DOUBLE_DOT:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];
	
	while ($out =~/(.*)\.(.*)\.(.*)\Z/)
	{
		if (!($2 =~ /\A\.\Z/))
		{
			$out = "$1$REWRITE_TO_CHAR$2.$3";
		}
		else 
		{
			$out = "$1$REWRITE_TO_CHAR.$3";
		}
		print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	}
	
	return ($out);
}

sub SQUASH_FILTER
{
	local ($in, $out, $string);

	print "SQUASH_FILTER:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	foreach $string (@FILTER_STRINGS)
	{
		$out =~ s/$string//ig;
		print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	}
	
	return ($out);
}

sub EXTN_REWRITE
{
	local ($in, $out, $temp_start, $temp_end, $new_extn);

	print "EXTN_REWRITE:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{
		if ($in =~/(.*)\.(.*)\Z/)
		{
			$temp_start = $1;
			$temp_end = $2;
			$temp_end =~ tr/[A-Z]/[a-z]/;
			$new_extn = $EXTN_REWRITE{$temp_end};
			if (defined($new_extn))
			{ 
				$out = "$temp_start.$new_extn";
			}
			else
			{
				print ("No new extension avaliable for the extension \'$temp_end\'. Please add an entry for this extension in the EXTN_REWRITE array.") if $DEBUG;
				if ($ALLOW_FOREIGN_EXTN)
				{
				}
				else
				{
					die("No foreign extensions allowed.\n") if $DEBUG;
				}
				$out = "$temp_start.$temp_end";
			}
		}
	}
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub ALL_UPPER
{
	local ($in, $out);

	print "ALL_UPPER:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ tr/[a-z]/[A-Z]/;
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub ALL_LOWER
{
	local ($in, $out);

	print "ALL_LOWER:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ tr/[A-Z]/[a-z]/;
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub LOWER_EXTN
{
	local ($in, $out, $temp_start, $temp_end);

	print "LOWER_EXTN:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{
		if ($in =~/(.*)\.(.*)\Z/)
		{
			$temp_start = $1;
			$temp_end = $2;
			$temp_end =~ tr/[A-Z]/[a-z]/;
			$out = "$temp_start.$temp_end";
		}
	}
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub CAP_AFTER
{
	local ($in, $out, $special, $esc_special, $tempchar);

	print "CAP_AFTER:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	foreach $special (@CAP_AFTER)
	{
		$esc_special = quotemeta($special);
		
		print "$special:\n" if $DEBUG;
		print "$out -> " if $DEBUG;
		
		while ($out =~ /$esc_special([a-z])/)
		{
			$tempchar = $1;
			$tempchar =~ tr/[a-z]/[A-Z]/;
		
			$out =~ s/$esc_special[a-z]/$special$tempchar/;
			
		}

		if ( $out =~ /\A([a-z])/ )
		{
			$tempchar = $1;
			$tempchar =~ tr/[a-z]/[A-Z]/;
			$out =~ s/\A[a-z]/$tempchar/;
		}
		
		print "$out\n" if $DEBUG;
	
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub CAP_LEADING
{
	local ($in, $out, $special, $esc_special, $tempchar);

	print "CAP_LEADING:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	
	if ( $out =~ /\A([a-z])/ )
	{
		$tempchar = $1;
		$tempchar =~ tr/[a-z]/[A-Z]/;
		$out =~ s/\A[a-z]/$tempchar/;
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub REWRITE_SPECIAL_CHARS
{
	local ($in, $out, $index, $items, $orig_char, $new_char, $srcidx, $destidx);

	print "REWRITE_SPECIAL_CHARS:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$items = @SPECIAL_REWRITE;
	$items = $items / 2;
	
	$index = 0;

	while ($index < $items)
	{	
		$srcidx = $index * 2;
		$destidx = ($index * 2) + 1;


		$orig_char = "$SPECIAL_REWRITE[$srcidx]";
		$new_char = $SPECIAL_REWRITE[$destidx];

		print "Rewriting \"$orig_char\" to \"$new_char\":\n" if $DEBUG;
		
		$orig_char = quotemeta($orig_char);

#		$new_char = quotemeta($new_char);

		print "Rewrite: $out -> " if $DEBUG;
		$out =~ s/$orig_char/$new_char/g;
		print "$out\n" if $DEBUG;
		
		
		$index++;		
	}

	if ($NO_DUP_SPECIAL)
	{
		$out = &SQUASH_DOUBLE ($out);		
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_PLUS
{
	local ($in, $out);

	print "SQUASH_PLUS:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\+//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_DASH
{
	local ($in, $out);

	print "SQUASH_DASH:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/-//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_BANG
{
	local ($in, $out);

	print "SQUASH_BANG:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/!//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_AMP
{
	local ($in, $out);

	print "SQUASH_AMP:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/&//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_AT
{
	local ($in, $out);

	print "SQUASH_AT:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\@//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_BACKSLASH
{
	local ($in, $out);

	print "SQUASH_BACKSLASH:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\\//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_CARAT
{
	local ($in, $out);

	print "SQUASH_CARAT:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\^//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_COLON
{
	local ($in, $out);

	print "SQUASH_COLON:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/://g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_DOLLAR
{
	local ($in, $out);

	print "SQUASH_DOLLAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\$//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_PERCENT
{
	local ($in, $out);

	print "SQUASH_PERCENT:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/%//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_PIPE
{
	local ($in, $out);

	print "SQUASH_PIPE:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\|//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_POUND
{
	local ($in, $out);

	print "SQUASH_POUND:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/#//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_SEMICOLON
{
	local ($in, $out);

	print "SQUASH_SEMICOLON:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/;//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_QUESTION
{
	local ($in, $out);

	print "SQUASH_QUESTION:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\?//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_STAR
{
	local ($in, $out);

	print "SQUASH_STAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\*//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_TICK
{
	local ($in, $out);

	print "SQUASH_TICK:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/`//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_TILDE
{
	local ($in, $out);

	print "SQUASH_TILDE:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/~//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_COMMA
{
	local ($in, $out);

	print "SQUASH_COMMA:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/,//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_UNDERSCORE
{
	local ($in, $out);

	print "SQUASH_UNDERSCORE:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/_//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_EQUAL
{
	local ($in, $out);

	print "SQUASH_EQUAL:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/=//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_DBLQUOT
{
	local ($in, $out);

	print "SQUASH_DBLQUOT:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/"//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_QUOT
{
	local ($in, $out);

	print "SQUASH_QUOT:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/'//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_PAREN
{
	local ($in, $out);

	print "SQUASH_PAREN:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\(//g;
	$out =~ s/\)//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_CURLY
{
	local ($in, $out);

	print "SQUASH_CURLY:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\{//g;
	$out =~ s/\}//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_SQUARE
{
	local ($in, $out);

	print "SQUASH_CURLY:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\[//g;
	$out =~ s/\]//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_ANGLE
{
	local ($in, $out);

	print "SQUASH_CURLY:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	$out =~ s/\<//g;
	$out =~ s/\>//g;

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_PRE_DOT_CHAR
{
	local ($in, $out, $pair_char, $pair_opposite, $char_count, $opposite_count);
	local ($out_filename, $out_extn, @temparray);

	print "SQUASH_PRE_DOT_CHAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$out_filename = $1;
		$out_extn = $2;

		$out_filename =~ s/$SPECIAL_CHAR_CLASS\Z//g;

		if ($out_filename =~ /.*($SPECIAL_PAIR_CLASS)\Z/)		
		{
			$pair_char = $1;
			$pair_opposite = $SPECIAL_PAIRS{$pair_char};
			$pair_char = quotemeta($pair_char);
			$pair_opposite = quotemeta($pair_opposite);

			$char_count = 0;
			$opposite_count = 0;
			while ($out_filename =~ /$pair_char/g)
			{
				$char_count++;
			}
			while ($out_filename =~ /$pair_opposite/g)
			{
				$opposite_count++;
			}

			if ($char_count > $opposite_count)
			{
				$out_filename =~ s/(.*)($SPECIAL_PAIR_CLASS)/$1/;
				
				$char_count = 0;
				$opposite_count = 0;
				while ($out_filename =~ /$pair_char/g)
				{
					$char_count++;
				}
				while ($out_filename =~ /$pair_opposite/g)
				{
					$opposite_count++;
				}
			}
			if ($char_count != $opposite_count)
			{
				if ($SQUASH_UNBALANCED_PAIR)
				{
					if (( $out_filename =~ /\(/ ) || ( $out_filename =~ /\)/ ))
					{
						$out_filename = &SQUASH_PAREN($out_filename);
					}
					if (( $out_filename =~ /\</ ) || ( $out_filename =~ /\>/ ))
					{
						$out_filename = &SQUASH_ANGLE($out_filename);
					}
					if (( $out_filename =~ /\{/ ) || ( $out_filename =~ /\}/ ))
					{
						$out_filename = &SQUASH_CURLY($out_filename);
					}
					if (( $out_filename =~ /\[/ ) || ( $out_filename =~ /\]/ ))
					{
						$out_filename = &SQUASH_SQUARE($out_filename);
					}
				}
			}

		}
		
		$out = "$out_filename.$out_extn";

	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_POST_DOT_CHAR
{
	local ($in, $out, $pair_char, $pair_opposite, $char_count, $opposite_count);
	local ($out_filename, $out_extn, @temparray);

	print "SQUASH_POST_DOT_CHAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$out_filename = $1;
		$out_extn = $2;

		$out_filename =~ s/\.$SPECIAL_CHAR_CLASS*/\./g;	# Get rid of the special chars before .
							# Then get rid of unbalanced brackets that exist

		if ($out_filename =~ /\.($SPECIAL_PAIR_CLASS)/)	# before the .		
		{
			$pair_char = $1;
			$pair_opposite = $SPECIAL_PAIRS{$pair_char};
			$pair_char = quotemeta($pair_char);
			$pair_opposite = quotemeta($pair_opposite);

			$char_count = 0;
			$opposite_count = 0;
			while ($out_filename =~ /$pair_char/g)
			{
				$char_count++;
			}
			while ($out_filename =~ /$pair_opposite/g)
			{
				$opposite_count++;
			}

			if ($char_count < $opposite_count)
			{
				$out_filename =~ s/(.*)($SPECIAL_PAIR_CLASS)/$1/;
				
				$char_count = 0;
				$opposite_count = 0;
				while ($out_filename =~ /$pair_char/g)
				{
					$char_count++;
				}
				while ($out_filename =~ /$pair_opposite/g)
				{
					$opposite_count++;
				}
			}
			if ($char_count != $opposite_count)
			{
				if ($SQUASH_UNBALANCED_PAIR)
				{
					if (( $out_filename =~ /\(/ ) || ( $out_filename =~ /\)/ ))
					{
						$out_filename = &SQUASH_PAREN($out_filename);
					}
					if (( $out_filename =~ /\</ ) || ( $out_filename =~ /\>/ ))
					{
						$out_filename = &SQUASH_ANGLE($out_filename);
					}
					if (( $out_filename =~ /\{/ ) || ( $out_filename =~ /\}/ ))
					{
						$out_filename = &SQUASH_CURLY($out_filename);
					}
					if (( $out_filename =~ /\[/ ) || ( $out_filename =~ /\]/ ))
					{
						$out_filename = &SQUASH_SQUARE($out_filename);
					}
				}
			}

		}
		
		$out = "$out_filename.$out_extn";
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_PRE_EXTN_CHAR
{
	local ($in, $out, $pair_char, $pair_opposite, $char_count, $opposite_count);
	local ($out_filename, $out_extn, @temparray);

	print "SQUASH_PRE_EXTN_CHAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$out_filename = $1;
		$out_extn = $2;

		$out_extn =~ s/$SPECIAL_CHAR_CLASS//g;		# Get rid of the special chars before .
								# Then get rid of unbalanced brackets that exist

		if ($out_extn =~ /\A($SPECIAL_PAIR_CLASS).*/)		
		{
			$pair_char = $1;
			$pair_opposite = $SPECIAL_PAIRS{$pair_char};
			$pair_char = quotemeta($pair_char);
			$pair_opposite = quotemeta($pair_opposite);

			$char_count = 0;
			$opposite_count = 0;
			while ($out_extn =~ /$pair_char/g)
			{
				$char_count++;
			}

			while ($out_extn =~ /$pair_opposite/g)
			{
				$opposite_count++;
			}

			if ($char_count > $opposite_count)
			{
				$out_extn =~ s/($SPECIAL_PAIR_CLASS)(.*)/$2/;
				
				$char_count = 0;
				$opposite_count = 0;
				while ($out_extn =~ /$pair_char/g)
				{
					$char_count++;
				}
				while ($out_extn =~ /$pair_opposite/g)
				{
					$opposite_count++;
				}
			}
			if ($char_count != $opposite_count)
			{
				if ($SQUASH_UNBALANCED_PAIR)
				{
					if (( $out_extn =~ /\(/ ) || ( $out_extn =~ /\)/ ))
					{
						$out_extn = &SQUASH_PAREN($out_extn);
					}
					if (( $out_extn =~ /\</ ) || ( $out_extn =~ /\>/ ))
					{
						$out_extn = &SQUASH_ANGLE($out_extn);
					}
					if (( $out_extn =~ /\{/ ) || ( $out_extn =~ /\}/ ))
					{
						$out_extn = &SQUASH_CURLY($out_extn);
					}
					if (( $out_extn =~ /\[/ ) || ( $out_extn =~ /\]/ ))
					{
						$out_extn = &SQUASH_SQUARE($out_extn);
					}
				}
			}
		}
		$out = "$out_filename.$out_extn";
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_POST_EXTN_CHAR
{
	local ($in, $out, $pair_char, $pair_opposite, $char_count, $opposite_count);
	local ($out_filename, $out_extn, @temparray);

	print "SQUASH_POST_EXTN_CHAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$out_filename = $1;
		$out_extn = $2;

		$out_extn =~ s/$SPECIAL_CHAR_CLASS*\Z//g;	# Get rid of the special chars before .
								# Then get rid of unbalanced brackets that exist

		if ($out_extn =~ /.*($SPECIAL_PAIR_CLASS)/)	# before the .		
		{
			$pair_char = $1;
			$pair_opposite = $SPECIAL_PAIRS{$pair_char};
			$pair_char = quotemeta($pair_char);
			$pair_opposite = quotemeta($pair_opposite);

			$char_count = 0;
			$opposite_count = 0;
			while ($out_extn =~ /$pair_char/g)
			{
				$char_count++;
			}
			while ($out_extn =~ /$pair_opposite/g)
			{
				$opposite_count++;
			}

			if ($char_count < $opposite_count)
			{
				$out_extn =~ s/(.*)($SPECIAL_PAIR_CLASS*)/$1/;
				
				$char_count = 0;
				$opposite_count = 0;
				while ($out_extn =~ /$pair_char/g)
				{
					$char_count++;
				}
				while ($out_extn =~ /$pair_opposite/g)
				{
					$opposite_count++;
				}
			}
			if ($char_count != $opposite_count)
			{
				if ($SQUASH_UNBALANCED_PAIR)
				{
					if (( $out_extn =~ /\(/ ) || ( $out_extn =~ /\)/ ))
					{
						$out_extn = &SQUASH_PAREN($out_extn);
					}
					if (( $out_extn =~ /\</ ) || ( $out_extn =~ /\>/ ))
					{
						$out_extn = &SQUASH_ANGLE($out_extn);
					}
					if (( $out_extn =~ /\{/ ) || ( $out_extn =~ /\}/ ))
					{
						$out_extn = &SQUASH_CURLY($out_extn);
					}
					if (( $out_extn =~ /\[/ ) || ( $out_extn =~ /\]/ ))
					{
						$out_extn = &SQUASH_SQUARE($out_extn);
					}
				}
			}
		}

		$out = "$out_filename.$out_extn";
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_LEADING_CHAR
{
	local ($in, $out);

	print "SQUASH_LEADING_CHAR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$out_filename = $1;
		$out_extn= $2;

		$out_filename =~ s/\A$SPECIAL_CHAR_CLASS(.*)/$1/;	# Get rid of the special chars before .
									# Then get rid of unbalanced brackets that exist

		if ($LEADING_CHAR_INC_PAIRS)
		{
			if ($out_filename =~ /\A($SPECIAL_PAIR_CLASS).*/)	
			{
				$pair_char = $1;
				$pair_opposite = $SPECIAL_PAIRS{$pair_char};
				$pair_char = quotemeta($pair_char);
				$pair_opposite = quotemeta($pair_opposite);
	
				$char_count = 0;
				$opposite_count = 0;
				while ($out_filename =~ /$pair_char/g)
				{
					$char_count++;
				}
	
				while ($out_filename =~ /$pair_opposite/g)
				{
					$opposite_count++;
				}
	
				if ($char_count > $opposite_count)
				{
					$out_filename =~ s/($SPECIAL_PAIR_CLASS)(.*)/$2/;
					
					$char_count = 0;
					$opposite_count = 0;
					while ($out_filename =~ /$pair_char/g)
					{
						$char_count++;
					}
					while ($out_filename =~ /$pair_opposite/g)
					{
						$opposite_count++;
					}
				}
				if ($char_count != $opposite_count)
				{
					if ($SQUASH_UNBALANCED_PAIR)
					{
						if (( $out_filename =~ /\(/ ) || ( $out_filename =~ /\)/ ))
						{
							$out_filename = &SQUASH_PAREN($out_filename);
						}
						if (( $out_filename =~ /\</ ) || ( $out_filename =~ /\>/ ))
						{
							$out_filename = &SQUASH_ANGLE($out_filename);
						}
						if (( $out_filename =~ /\{/ ) || ( $out_filename =~ /\}/ ))
						{
							$out_filename = &SQUASH_CURLY($out_filename);
						}
						if (( $out_filename =~ /\[/ ) || ( $out_filename =~ /\]/ ))
						{
							$out_filename = &SQUASH_SQUARE($out_filename);
						}
					}
				}
			}
		}
		
		$out = "$out_filename.$out_extn";
	}
	else
	{			
		$out =~ s/\A$SPECIAL_CHAR_CLASS//;	# Get rid of the special chars before .
								# Then get rid of unbalanced brackets that exist

		if ($LEADING_CHAR_INC_PAIRS)
		{
			if ($out =~ /\b($SPECIAL_PAIR_CLASS).*/)	# before the .		
			{
				$pair_char = $1;
				$pair_char = quotemeta($pair_char);
				$pair_opposite = $SPECIAL_PAIRS{$pair_char};
				$pair_opposite = quotemeta($pair_opposite);
	
				$char_count = 0;
				$opposite_count = 0;
				while ($out =~ /$pair_char/g)
				{
					$char_count++;
				}
	
				while ($out =~ /$pair_opposite/g)
				{
					$opposite_count++;
				}
	
				if ($char_count > $opposite_count)
				{
					$out =~ s/($SPECIAL_PAIR_CLASS)(.*)/$2/;
					
					$char_count = 0;
					$opposite_count = 0;
					while ($out =~ /$pair_char/g)
					{
						$char_count++;
					}
					while ($out =~ /$pair_opposite/g)
					{
						$opposite_count++;
					}
				}
				if ($char_count != $opposite_count)
				{
					if ($SQUASH_UNBALANCED_PAIR)
					{
						if (( $out =~ /\(/ ) || ( $out =~ /\)/ ))
						{
							$out = &SQUASH_PAREN($out);
						}
						if (( $out =~ /\</ ) || ( $out =~ /\>/ ))
						{
							$out = &SQUASH_ANGLE($out);
						}
						if (( $out =~ /\{/ ) || ( $out =~ /\}/ ))
						{
							$out = &SQUASH_CURLY($out);
						}
						if (( $out =~ /\[/ ) || ( $out =~ /\]/ ))
						{
							$out = &SQUASH_SQUARE($out);
						}
					}
				}
			}
		}
		$out = "$out_filename.$out_extn";
	}	
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_EXTN_PAIR 
{
	local ($in, $out, $pair_char, $pair_opposite);

	print "SQUASH_EXTN_PAIR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$out_filename = $1;
		$out_extn = $2;

		$out_extn =~ s/$SPECIAL_PAIR_CLASS//g;		

		$out = "$out_filename.$out_extn";
	}
	
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_DOUBLE 
{
	local ($in, $out, $special, $esc_special);

	print "SQUASH_DOUBLE:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	foreach $special (@SPECIALS)
	{
		$esc_special = quotemeta($special);

		$out =~ s/$esc_special+/$special/g;

		print "$special: $out\n" if $DEBUG;

	}
	$out =~ s/\\//g; 	# Frustration fix #2
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub SQUASH_UNBALANCED_PAIR
{
	local ($in, $out, $pair_char, $pair_opposite, $char_count, $opposite_count);
	local (@temparray);

	print "SQUASH_UNBALANCED_PAIR:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if ($out =~ /.*($SPECIAL_PAIR_CLASS)/)
	{
		$pair_char = "$1";
		$pair_opposite = $SPECIAL_PAIRS{$pair_char};
		$pair_char = quotemeta($pair_char);
		$pair_opposite = quotemeta($pair_opposite);

#print "Char: $pair_char Opposite: $pair_opposite\n";


		$char_count = 0;
		$opposite_count = 0;
		while ($out =~ /$pair_char/g)
		{
			$char_count++;
		}
		while ($out =~ /$pair_opposite/g)
		{
			$opposite_count++;
		}

		
		if ($char_count > $opposite_count)
		{
			$out =~ s/(.*)($SPECIAL_PAIR_CLASS)/$1/;
			
			$char_count = 0;
			$opposite_count = 0;
			while ($out =~ /$pair_char/g)
			{
				$char_count++;
			}
			while ($out =~ /$pair_opposite/g)
			{
				$opposite_count++;
			}
		}
		if ($char_count == $opposite_count)
		{
			if ($char_count == 1)
			{
				if ( $out =~ /\).*\(/ )
				{
					$out = &SQUASH_PAREN($out);
				}
				if ( $out =~ /\>.*\</ )
				{
					$out = &SQUASH_ANGLE($out);
				}
				if ( $out =~ /\}.*\{/ )
				{
					$out = &SQUASH_CURLY($out);
				}
				if ( $out =~ /\].*\[/)
				{
					$out = &SQUASH_SQUARE($out);
				}
			}
		}
		else
		{
			if (( $out =~ /\(/ ) || ( $out =~ /\)/ ))
			{
				$out = &SQUASH_PAREN($out);
			}
			if (( $out =~ /\</ ) || ( $out =~ /\>/ ))
			{
				$out = &SQUASH_ANGLE($out);
			}
			if (( $out =~ /\{/ ) || ( $out =~ /\}/ ))
			{
				$out = &SQUASH_CURLY($out);
			}
			if (( $out =~ /\[/ ) || ( $out =~ /\]/ ))
			{
				$out = &SQUASH_SQUARE($out);
			}
		}
	}

	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub GET_SERIAL_NAME
{
	local ($in, $out, $name, $basename, $extn, $serial, $rewrite_cksum, $disk_cksum);

	print "GET_SERIAL_NAME:\n" if $DEBUG;

	$in = $_[0];
	$out = $_[0];

	if (!$NODOT_FLAG)
	{			
		$out =~ /(.*)\.(.*)\Z/;			# Split up filename and extension. 
							
		$name = $1;
		$extn = $2;
							# Split up main filename and serial
		if ($name =~ /(.*)$SERIAL_SYMBOL_CLASS(\d{1,4})\Z/)
		{
			$basename = $1;
			$serial = $2;
			print "Previous serial found: $serial\n" if $DEBUG;
		}
		else
		{
			$basename = $name;
			print "No previous serial found\n" if $DEBUG;
		}
		# After stripping of serial it didn't conflict another file, so keep it without the serial
		if ( !(-e "$DIRECTORY$basename.$extn") )
		{
			$out = "$DIRECTORY$basename.$extn";
			$SERIAL_FOUND = 1;
		}
		else # Stripping off of serial found a possible filename but it might be same file
		{
			if ($NOTUNIX)	# Not a UNIX OS
			{
				# If it is the same file with the exception of minor case changes
				rename ($FILENAME, "$FILENAME.tmp");
				if ( !(-e "$DIRECTORY$basename.$extn")) # Whoops! Same file.
				{
					rename ("$FILENAME.tmp", $FILENAME);
					# Hit special non UNIX capitrization case
					$SAME_FILE = 1;
					print "SAME_FILE Hit.\n" if $DEBUG;
				}
				else 	# The propsed name and the orginal name are different files
				{
					rename ("$FILENAME.tmp", $FILENAME);
					$rewrite_cksum = &CKSUM("$FILENAME");
					$disk_cksum = &CKSUM("$DIRECTORY$basename.$extn");
					print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
					if ($rewrite_cksum == $disk_cksum)
					{
						$out = "$DIRECTORY$basename.$extn";
						$DELETE_ME_FLAG = 1;
						print "Hit diffname-notunix-notcap-dup case.\n" if $DEBUG;
					}
					else
					{	
						print "Going to obtain serial (NOT-UNIX non-dup case)\n" if $DEBUG;
					}

				}
			}
			else		# Oh, it's a nice UNIX OS
			{
				$rewrite_cksum = &CKSUM("$FILENAME");
				$disk_cksum = &CKSUM("$DIRECTORY$basename.$extn");
				print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
				if ($rewrite_cksum == $disk_cksum)
				{
					$out = "$DIRECTORY$basename.$extn";
					$DELETE_ME_FLAG = 1;
					print "Hit samename-normal-dup case.\n" if $DEBUG;
				}
				else
				{
					print "Going to obtain serial (Standard non-dup case)\n" if $DEBUG;
				}
			}
		}
		
		$serial = sprintf("%03d", 1);			# Set serial to 001
		# Checking the new proposed serial
		while ( !($SERIAL_FOUND || $DELETE_ME_FLAG || $SAME_FILE) )	# No filename found yet and no file duplicate
		{
			# If the serialed name matches one on disk then check filename
			if (-e "$DIRECTORY$basename$SERIAL_SYMBOL$serial.$extn")
			{
				if ($NOTUNIX) 
				{
					# If it is the same file with the exception of minor case changes
					rename ($FILENAME, "$FILENAME.tmp");
					if ( !(-e "$DIRECTORY$basename.$extn")) # It is the same file
					{
						rename ("$FILENAME.tmp", $FILENAME);
						$SAME_FILE = 1;
						print "Hit serial-samefile-notunix-cap case.\n" if $DEBUG;
					}
					else
					{
						rename ("$FILENAME.tmp", $FILENAME);
						$rewrite_cksum = &CKSUM("$FILENAME");
						$disk_cksum = &CKSUM("$DIRECTORY$basename$SERIAL_SYMBOL$serial.$extn");
						print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
						if ($rewrite_cksum == $disk_cksum)
						{
							$out = "$DIRECTORY$basename.$extn";
							$DELETE_ME_FLAG = 1;
							print "Hit serial-diffname-notunix-notcap case.\n" if $DEBUG;
						}
						else
						{	
							$serial++;
							$serial = sprintf("%03d",$serial);
							print "Going to try serial $serial\n" if $DEBUG;
						}
					}
				}
				else
				{
					$rewrite_cksum = &CKSUM("$FILENAME");
					$disk_cksum = &CKSUM("$DIRECTORY$basename$SERIAL_SYMBOL$serial.$extn");
					print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
					if ($rewrite_cksum == $disk_cksum)
					{
						$out = "$DIRECTORY$basename$SERIAL_SYMBOL$serial.$extn";
						$DELETE_ME_FLAG = 1;
						print "Hit samename-normal-dup case.\n" if $DEBUG;
					}
					else
					{
						$serial++;
						$serial = sprintf("%03d",$serial);
						print "Going to try serial $serial\n" if $DEBUG;

					}
				}
			}
			# Since the serialed name didn't match a file on the disk then
			# we found our filename
			else
			{
				$out = "$DIRECTORY$basename$SERIAL_SYMBOL$serial.$extn";
				$SERIAL_FOUND = 1;
			}
		}
	}
	else	# No dot in this filename
	{										
		$name = $out;
				
		if ($name =~ /(.*)$SERIAL_SYMBOL_CLASS(\d{1,4})\Z/)
		{
			$basename = $1;
			$serial = $2;
			print "Previous serial found: $serial\n" if $DEBUG;
		}
		else
		{
			$basename = $name;
			print "No previous serial found\n" if $DEBUG;
		}

		if ( !(-e "$DIRECTORY$basename") )		# Stripping the serial matched to 
								# a unique name
		{
			$out = "$DIRECTORY$basename";
			$SERIAL_FOUND = 1;
		}
		else
		{
			if ($NOTUNIX)
			{
				# If it is the same file with the exception of minor case changes
				rename ($FILENAME, "$FILENAME.tmp");
				if ( !(-e "$DIRECTORY$basename")) # It is the same file
				{
					rename ("$FILENAME.tmp", $FILENAME);
					# Hit special non UNIX capitrization case
					$SAME_FILE = 1;
					print "SAME_FILE Hit.\n" if $DEBUG;
				}
				else
				{
					rename ("$FILENAME.tmp", $FILENAME);
					$rewrite_cksum = &CKSUM("$FILENAME");
					$disk_cksum = &CKSUM("$DIRECTORY$basename");
					print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
					if ($rewrite_cksum == $disk_cksum)
					{
						$out = "$DIRECTORY$basename";
						$DELETE_ME_FLAG = 1;
						print "Hit diffname-notunix-notcap-dup case.\n" if $DEBUG;
					}
					else
					{	
						print "Going to obtain serial (NOT-UNIX non-dup case)\n" if $DEBUG;
					}

				}
			}
			else
			{
				$rewrite_cksum = &CKSUM("$FILENAME");
				$disk_cksum = &CKSUM("$DIRECTORY$basename");
				print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
				if ($rewrite_cksum == $disk_cksum)
				{
					$out = "$DIRECTORY$basename";
					$DELETE_ME_FLAG = 1;
					print "Hit samename-normal-dup case.\n" if $DEBUG;
				}
				else
				{
						print "Going to obtain serial (Standard non-dup case)\n" if $DEBUG;
				}
			}
		}

		$serial = sprintf("%03d", 1);			# Set serial to 001

		while ( !($SERIAL_FOUND || $DELETE_ME_FLAG) )	# No filename found yet and no file duplicate
		{
			if (-e "$DIRECTORY$basename$SERIAL_SYMBOL$serial")
			{
				if ($NOTUNIX)
				{

					# If it is the same file with the exception of minor case changes
					rename ($FILENAME, "$FILENAME.tmp");
					if ( !(-e "$DIRECTORY$basename")) # It is the same file
					{
						rename ("$FILENAME.tmp", $FILENAME);
						# Hit special non UNIX capitrization case
						$SAME_FILE = 1;
						print "Hit serial-dup-notunix-cap case.\n" if $DEBUG;
					}
					else # It is a different file
					{
						rename ("$FILENAME.tmp", $FILENAME);
						$rewrite_cksum = &CKSUM("$FILENAME");
						$disk_cksum = &CKSUM("$DIRECTORY$basename$SERIAL_SYMBOL$serial");
						print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
						if ($rewrite_cksum == $disk_cksum)
						{
							$out = "$DIRECTORY$basename";
							$DELETE_ME_FLAG = 1;
							print "Hit serial-diffname-notunix-notcap case.\n" if $DEBUG;
						}
						else
						{	
							$serial++;
							$serial = sprintf("%03d",$serial);
							print "Going to try serial $serial\n" if $DEBUG;
						}
					}

				}
				else
				{
					$rewrite_cksum = &CKSUM("$FILENAME");
					$disk_cksum = &CKSUM("$DIRECTORY$basename$SERIAL_SYMBOL$serial");
					print "Checksums- Disk: $disk_cksum Rewrite: $rewrite_cksum\n" if $DEBUG;
					if ($rewrite_cksum == $disk_cksum)
					{
						$out = "$DIRECTORY$basename$SERIAL_SYMBOL$serial";
						$DELETE_ME_FLAG = 1;
						print "Hit samename-normal-dup case.\n" if $DEBUG;
					}
					else
					{
						$serial++;
						$serial = sprintf("%03d",$serial);
						print "Going to try serial $serial\n" if $DEBUG;

					}
				}
			}
			else
			{
				$out = "$DIRECTORY$basename$SERIAL_SYMBOL$serial";
				$SERIAL_FOUND = 1;
			}
		}
	}
				
	print "IFile: $in\nOFile: $out\n\n" if $DEBUG;
	
	return ($out);
}

sub DELETE_FILE
{
	local ($original, $new, $temp_input, $got_input);

	print "DELETE_FILE:\n" if $DEBUG;

	$original = $_[0];
	$new = $_[1];
	
	if ($FILE_SAFE)
	{
		if ($DEBUG)
		{
			if (-W $original)
			{
				print "File is unlinkable.\n";
			}
			else
			{
				if (-e $original)
				{
					print "File exists, but may be unlinkable due to lack of file permission.\n";
				}
			}
		}
				
		print "FILE_SAFE (-t): Suppressing unlink of $original.\n";
	}
	else
	{
		if ($INTERACT_FLAG || $DBL_INTERACT_FLAG)
		{
			$got_input = 0;
			$temp_input = "x"; # A first case workaround for WIN platform and getc
			while (!$got_input)
			{
				if ($temp_input =~ /\w/)
				{
					print "\nThe file $original is duplicated by another file on disk. Delete (y/n)? ";
				}
				$temp_input = getc;
				if ($temp_input =~ /y/i)
				{
					if (-W $original)
					{
						unlink($original) || print "Unable to unlink $original for unknown reason.\n";
						print "File deleted.\n";
						$got_input = 1;
						print "got_input flag set\n" if $DEBUG;
					}
					else
					{
						unlink($original) || print "Unable to unlink $original due to lack of file permission.\n";
						print "File deleted.\n";
						$got_input = 1;
						print "got_input flag set\n" if $DEBUG;
					}
				}
				elsif ($temp_input =~ /n/i)
				{
					$got_input = 1;
					print "got_input flag set\n" if $DEBUG;					
					print "File not deleted.\n" if $DEBUG;
				}
			}
		}
		else
		{
			if (-W $original)
			{
				unlink($original) || print "Unable to unlink $original for unknown reason.\n";
				print "File deleted.\n" if $DEBUG;
			}
			else
			{
				unlink($original) || print "Unable to unlink $original due to lack of file permission.\n";
				print "File deleted.\n" if $DEBUG;
			}
		}
	}
	
	print "DELETE_FILE finished\n" if $DEBUG;
	
	return (1);
}

sub RENAME_FILE
{
	local ($original, $new, $temp_input, $got_input);

	print "RENAME_FILE:\n" if $DEBUG;

	$original = $_[0];
	$new = $_[1];
	
	if ($FILE_SAFE)
	{
		if ($DEBUG)
		{
			if (-W $original)
			{
				print "Source is unlinkable.\n";
			}
			else
			{
				if (-e $original)
				{
					print "Source file exists, but may be unlinkable due to lack of file permission.\n";
				}
			}
			if (-e $new)
			{
				if ($SAME_FILE)
				{
					print "When attempting to test the rename, the destination filename already "; 
					print "exists -- overridden due to captailaization case on non-UNIX systems.\n";
				}
				else
				{
					die ("Internal error. When attempting to test the rename, the destination filename already exists.\n");
				}
			}
			else
			{
				open (TEST, ">$new") || print "Unable to create file $new.\n";
				close (TEST);
				unlink($new) || print "Unable to delete test file new.\n";
			}	
		}
		print "FILE_SAFE (-t): Suppressing rename of $original -> $new.\n";
				
	}
	else
	{
		if ($DBL_INTERACT_FLAG)
		{
			$temp_input = "x"; # A first case workaround for WIN platform and getc
			$got_input = 0;
			while (!$got_input)
			{
				if ($temp_input =~ /\w/)
				{
					print "\nThe file $original should be rewritten to $new. Rename (y/n)? ";
				}
				$temp_input = getc;
				if ($temp_input =~ /y/i)
				{
					if ($SAME_FILE) 
					{
						print "Same file. Not renaming...\n" if $DEBUG;
					}
					else
					{
						if ( (-W $original) && !(-e $new) )
						{
							rename($original,$new) || print "Unable to rename $original to $new for unknown reason.\n";
							print "File Renamed.\n";
							$got_input = 1;
							print "got_input flag set\n" if $DEBUG;
						}
						else
						{
							rename($original,$new) || print "Rename error: Unable to unlink $original due to lack of file permission or previous existance of destination file $new.\n";
							print "File renamed.\n";
							$got_input = 1;
							print "got_input flag set\n" if $DEBUG;
						}
						if ($VERBOSE_FLAG)
						{
							print "$original -> $new\n";
						}
					}
				}
				elsif ($temp_input =~ /n/i)
				{
					$got_input = 1;
					print "got_input flag set\n" if $DEBUG;					
					print "File not renamed.\n" if $DEBUG;
					
				}
			}
		}
		else
		{
			if ($SAME_FILE) 
			{
				print "Same file. Not renaming...\n" if $DEBUG;
			}
			else
			{
				if ( (-W $original) && !(-e $new) )
				{
					rename($original,$new) || print "Unable to rename $original to $new for unknown reason.\n";
					print "File renamed.\n" if $DEBUG;
				}
				else
				{
					rename($original,$new) || print "Rename error: Unable to unlink $original due to lack of file permission or previous existance of destination file $new.\n";
					print "File renamed.\n" if $DEBUG;
				}
				if ($VERBOSE_FLAG)
				{
					print "$original -> $new\n";
				}
			}
		}
	}
	
	print "RENAME_FILE finished\n" if $DEBUG;
	
	return (1);
}

