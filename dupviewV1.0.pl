#! /usr/bin/perl -w
########################################################################
#
#	Duplicate file checker log file viewer 		Version 1.0
#
#	Interactively processes the log file and allows the user 
#	to view and delete files
#
#	By: Chris McCluskey	Current Date: 20020728
#
########################################################################
# 
# HISTORY:
# 
#	
# TODO:
# ?. 
# ?. 
#
# RULES:
# $CURRENT_LINE must be on an VALUE: line.
########################################################################

use strict;		# Strict type variable checking
use Cwd;		# Used in finding working dir in ADDFILES

			
###############################

###############################

my $OS='win';		# What OS is this for (implemeted mac/unix/win)

###############################

my $DEBUG = 1;
my $CONFIRM = 1;
my $REPORT_FILE = "-none-";	# Set varible to send report file to disk
my $FILE_SAFE = 0;
my $CONFIRMATION = 1;		# Require confirmation before file delete

#my ($BASE_DIR, $DIRSEP, $ENTRYSEP, $DB_DIR, $TEMP_DIR);
#if ($OS eq 'mac')
#{ 
#	# You'll probably need to change $BASE_DIR
#	$BASE_DIR = 'Hard Drive'; $DIRSEP = ':'; $ENTRYSEP='::';
#	$DB_DIR = "$BASE_DIR".".imgfiles"; # Directory containing the FileDBs
#	$TEMP_DIR = getcwd();
#}
#elsif ($OS eq 'unix')
#{ 
#	$BASE_DIR = '/'; $DIRSEP = '/'; $ENTRYSEP = '/'; 
#	$DB_DIR = "$BASE_DIR"."root$DIRSEP".".imgfiles"; # Directory containing the FileDBs
#	$TEMP_DIR = getcwd();
#}
#elsif ($OS eq 'win')
#{
#	# You'll probably need to change $BASE_DIR
#	$BASE_DIR = 'c:/'; $DIRSEP = '/'; $ENTRYSEP = '/'; 
#	$DB_DIR = "$BASE_DIR".".imgfiles"; # Directory containing the FileDBs
#	$TEMP_DIR = "$BASE_DIR".".tempfiles"; # Directory containing the temporary entries used in processing
#}
#else
#{
#	$BASE_DIR = '/';
#	$DIRSEP = '/';		# The directory item speartor for platform used
#	$DB_DIR = "$BASE_DIR".".imgfiles"; # Directory containing the FileDBs
#	$TEMP_DIR = getcwd();
#}

my $VERSION = '1.0';
my $QUITTING = 0;
my @FILELINES;			# Array of the log file
my $STATUS = "No status.";
my @FILES;			# Files under review
my @FILESTATUS;			# Status of files under review
my @FILESIZE;
my $TEST_TYPE = "-unknown-";	# Current test type of the files being analyzed
my $CURRENT_LINE = 0;		# Current line being processed
my $TOTAL_LINE = 0;		# Total lines in file
my $ENTRY = "-unknown-";	# Key or entry for filegroup
#my $INDEX;
########################################################################

sub INIT_PROG
{
	my $FLAGTEST;
	while ($FLAGTEST = shift(@ARGV))
	{
		print "DEBUG: FLAGTEST: $FLAGTEST\n" if $DEBUG;
		if ($FLAGTEST =~ /\A-/)
		{		
			if ($FLAGTEST =~ /-d\b/)
			{
				$DEBUG = 1;
				print "DEBUG: DEBUG set\n" if $DEBUG;
			}
			elsif ($FLAGTEST =~ /-nc\b/)
			{
				$CONFIRMATION = 0;
				print "DEBUG: CONFIRMATION removed\n" if $DEBUG;
			}
			elsif ($FLAGTEST =~ /-f\b/)
			{
				
				$REPORT_FILE = shift(@ARGV);
				if (defined($REPORT_FILE))
				{
					if ($REPORT_FILE =~ /^-/)
					{
						die ("Invalid file supplied on command line.\n");
					}
					else
					{
						
						print "DEBUG: REPORT_FILE read as $REPORT_FILE\n" if $DEBUG;
						$REPORT_FILE =~ s/\\/\//g;
						open (REPORT, "$REPORT_FILE") || die ("Unable to open $REPORT_FILE for reading");  
						print "DEBUG: REPORT_FILE set to $REPORT_FILE\n" if $DEBUG;
						close (REPORT);
						&ERASE_ARRAY(\@FILELINES);
						&POPULATE_ARRAY;
						$STATUS = "Logfile $REPORT_FILE loaded";
					}
				}
				else
				{
					die("Filename switch set but no file name supplied.\n");
				}
			}
			elsif ($FLAGTEST =~ /-fs\b/)
			{
				$FILE_SAFE = 1;
				print "DEBUG: FILE_SAFE set\n" if $DEBUG;
			}
			else
			{
				die("Unsupported argument $FLAGTEST.\n");
			}
		}
		else
		{
			die("Unsupported argument $FLAGTEST.\n");
		}
	}
	
	# Goto first file
	&LOCK(1);
	&LOAD;
}

sub DISPLAY_PANEL
{
	$TOTAL_LINE = @FILELINES;
		#0123456789012345678901234567890123456789012345678901234567890123456789|123456789
	print 	"________________________________________________________________________________\n";
	printf	"Test type: %-15.15s\t", $TEST_TYPE;
	printf	"Version: %3.3s\t\t", $VERSION;
	printf	"Line %6.1d / %6.1d\t", $CURRENT_LINE, $TOTAL_LINE;
	printf	"\n";
	printf	"Entry: %-73.70s\n", $ENTRY;
	printf	"Logfile: %-70.70s\n", $REPORT_FILE; 
	printf	"Status: %-72.70s\n", $STATUS;
	print	">>> ";
	return(0);
}
 
sub GET_RESPONSE
{
	my $input;
	my $byte_count;

	# Had to use the sysread command here, because the STDIN glob just kept 
	# fucking up
DOAGAIN:

	$byte_count = sysread (STDIN, $input, 256);
	
	print "DEBUG: GET_RESPONSE: bytecount received is $byte_count\n" if $DEBUG;
	
	if (!($input =~ /\w|\n/))
	{
		print "DEBUG: GET_RESPONSE: Hit undefined case.\n" if $DEBUG;
		goto DOAGAIN;
	}
 
	$input =~ s/\t|\n|\r|\"//g;

	print "DEBUG: GET_RESPONSE: Returning input as \"$input\"\n" if $DEBUG;
	return ($input);
}


sub SET_INFILE
{
	my $fname;
	
	print "\n\n";
	print "Please enter the full path of the log file:\n";
	$fname = &GET_RESPONSE;
	$fname =~ s/\\/\//g;
	open (REPORT, "$fname");
	if (!(-e $fname))
	{
		print "\nUnable to open logfile.\n";
		$STATUS = "Unable to load new logfile. Using logfile $REPORT_FILE.";
		&PAUSE;
		goto END;
	}
	else
	{
		$REPORT_FILE = $fname;
		$STATUS = "New logfile $REPORT_FILE loaded";
	}
	close (REPORT);
	&ERASE_ARRAY(\@FILELINES);
	&POPULATE_ARRAY;
END:
}

sub PAUSE
{
	&GET_RESPONSE();
}

sub SPLAT
{
	my $lines = 100;
	my $count;
	
	for ($count = 0; $count < $lines; $count++)
	{
		print "\n";
	}
}

sub ERASE_ARRAY
{
	my $junk;
	my $array_pointer = $_[0];
	
	while ($junk = pop(@$array_pointer) )
	{
#		print "DEBUG: ERASE_ARRAY: Removed $junk form array.\n" if $DEBUG;
	}
}

sub POPULATE_ARRAY
{
	open (LOGFILE, $REPORT_FILE) || die ("Unable to load log file $REPORT_FILE for loading\n");
	binmode LOGFILE;
	
	my @linearr;
	my $entcount;
	my $dataline;
	while ($dataline = <LOGFILE>)
	{
		if ($dataline =~ /.*\n.*/)
		{
			@linearr = split("\n", $dataline);
			$entcount = @linearr;
#			print "DEBUG: POPULATE_ARRAY: Multiple records found in dataline. Found $entcount records.\n" if $DEBUG;
			$dataline = shift(@linearr);		
		}
ANOTHERRECORD:
		push(@FILELINES,$dataline);
		# Are there still remaining entries in the file array
		if ($dataline = shift(@linearr))
		{
			goto ANOTHERRECORD;
		}
	}
	close (LOGFILE);
	$TOTAL_LINE = @FILELINES;
	print "DEBUG: POPULATE_ARRAY: $TOTAL_LINE lines in line array\n" if $DEBUG;
}

sub LOCK
{
	my $action = $_[0];
	my $notlocked = 1;
#	my $go_back_one_more = 1;
	my $void;
	my $small_entry;
	
	my $snapstate_current_line = $CURRENT_LINE;
	my $snapstate_test_type = $TEST_TYPE;
	my $snapstate_entry = $ENTRY;
	
	print "DEBUG: LOCK: Action received as: $action.\n" if $DEBUG;
	# If it going to go backwards do one loop
	if ($action =~ /b/)
	{
		if ($FILELINES[$CURRENT_LINE] =~ /^TYPE:/) # Simple backwards hit-already condition
		{
			$CURRENT_LINE--;
		}
		while ($notlocked && ($CURRENT_LINE >= 0)) # If we haven't found it going backwards
		{
			if ($FILELINES[$CURRENT_LINE] =~ /^TYPE:/)
			{
				($void, $TEST_TYPE) = split (/:/, $FILELINES[$CURRENT_LINE], 2);
				$TEST_TYPE =~ s/\s//g;
				$notlocked = 0;
				$ENTRY = "-unknown-";
				$STATUS = "Locked onto test type $TEST_TYPE";
				print "DEBUG: LOCK: Backwards - Action test type found.\n" if $DEBUG;
			}
			else
			{
				$CURRENT_LINE--;
				$TEST_TYPE = "unknown";
#				print "DEBUG: LOCK: Backwards - Looking for previous entry... Test type now invalid.\n" if $DEBUG;
			}
		}
		
		if ($CURRENT_LINE < 0)
		{
			print "DEBUG: LOCK: Backwards - A top of file. Enabling snapstate.\n" if $DEBUG;
			$CURRENT_LINE = $snapstate_current_line;
			$TEST_TYPE = $snapstate_test_type;
			$ENTRY = $snapstate_entry;
			$STATUS = "Start of file reached.";
		}
	}
	elsif ($action =~ /f/)
	{
		if ($FILELINES[$CURRENT_LINE] =~ /^TYPE:/) # Simple forward hit-already condition
		{
			$CURRENT_LINE++;
		}
		while ($notlocked && ($CURRENT_LINE < $TOTAL_LINE)) # If we haven't found it going forwards
		{
			if ($FILELINES[$CURRENT_LINE] =~ /^TYPE:/)
			{
				($void, $TEST_TYPE) = split (/:/, $FILELINES[$CURRENT_LINE], 2);
				$TEST_TYPE =~ s/\s//g;
				$notlocked = 0;
				$ENTRY = "-unknown-";
				$STATUS = "Locked onto test type $TEST_TYPE";
				print "DEBUG: LOCK: Forwards - Action test type found.\n" if $DEBUG;
			}
			else
			{
				$CURRENT_LINE++;
			}
		}
		if ($CURRENT_LINE == $TOTAL_LINE)
		{
			print "DEBUG: LOCK: Forwards - At bottom of file. Enabling snapstate.\n" if $DEBUG;
			$CURRENT_LINE = $snapstate_current_line;
			$TEST_TYPE = $snapstate_test_type;
			$ENTRY = $snapstate_entry;
			$STATUS = "End of file reached.";
		}
	}
	elsif ($action < 0)
	{	
		while ($notlocked && ($CURRENT_LINE >= 0)) # If we haven't found it going backwards
		{
			$CURRENT_LINE--;
			if ($FILELINES[$CURRENT_LINE] =~ /^TYPE:/)
			{
				$TEST_TYPE = "unknown";
				print "DEBUG: LOCK: Backwards - Looking for previous entry... Test type now invalid.\n" if $DEBUG;
			}
			if ($FILELINES[$CURRENT_LINE] =~ /^ENTRY:/)
			{
				$action++;
				if ($action < 0)
				{
					print "DEBUG: LOCK: Backwards - Found an entry. Action at $action.\n" if $DEBUG;
				}
				else
				{
					$notlocked = 0;
					($void, $small_entry) = split (/:/, $FILELINES[$CURRENT_LINE], 2);
					$small_entry =~ s/\n|\r//g;
					$ENTRY = $small_entry;
					$STATUS = "Locked onto entry $small_entry";
					print "DEBUG: LOCK: Backwards - At required entry. Action at $action.\n" if $DEBUG;
				}
			}
		}
		if ($CURRENT_LINE < 0)
		{
			print "DEBUG: LOCK: Backwards - A top of file. Enabling snapstate.\n" if $DEBUG;
			$CURRENT_LINE = $snapstate_current_line;
			$TEST_TYPE = $snapstate_test_type;
			$ENTRY = $snapstate_entry;
			$STATUS = "Top of file reached.";
		}
	}
	elsif ($action > 0)
	{
		while ($notlocked && ($CURRENT_LINE < $TOTAL_LINE)) # If we haven't found it going forwards
		{
			$CURRENT_LINE++;
			if ($FILELINES[$CURRENT_LINE] =~ /^TYPE:/)
			{
				if ($action =~ /f/)
				{
					($void, $TEST_TYPE) = split (/:/, $FILELINES[$CURRENT_LINE], 2);
					$notlocked = 0;
					print "DEBUG: LOCK: Forwards - Action test type found.\n" if $DEBUG;
				}
			}
			if ($FILELINES[$CURRENT_LINE] =~ /^ENTRY:/)
			{
				$action--;
				if ($action > 0)
				{
					print "DEBUG: LOCK: Forwards - Found an entry. Action at $action.\n" if $DEBUG;
				}
				else
				{
					$notlocked = 0;
					($void, $small_entry) = split (/:/, $FILELINES[$CURRENT_LINE], 2);
					$small_entry =~ s/\n|\r//g;
					$ENTRY = $small_entry;
					$STATUS = "Locked onto entry $small_entry";
					print "DEBUG: LOCK: Forwards - At required entry. Action at $action.\n" if $DEBUG;
				}
			}
		}
		if ($CURRENT_LINE == $TOTAL_LINE)
		{
			print "DEBUG: LOCK: Forwards - At bottom of file. Enabling snapstate.\n" if $DEBUG;
			$CURRENT_LINE = $snapstate_current_line;
			$TEST_TYPE = $snapstate_test_type;
			$ENTRY = $snapstate_entry;
			$STATUS = "End of file reached.";
		}
	}
	else
	{
		print "DEBUG: LOCK: Um... Wierd action state. Just entered Twilight Zone.\n" if $DEBUG;
	}
}

sub LOAD
{
	my $mini_index = -1;
	my ($void, $small_entry);
	my $original_current_line = $CURRENT_LINE;
	my $line;
	
	$TOTAL_LINE = @FILELINES;

	# If no confirmation delete
	if (!($CONFIRMATION))
	{
		&DO_DELETE;
		print "DEBUG: LOAD: No confirmation - Doing DO_DELETE\n" if $DEBUG;
	}
	
	# clear arrays
	&ERASE_ARRAY(\@FILES);
	&ERASE_ARRAY(\@FILESTATUS);
	&ERASE_ARRAY(\@FILESIZE);
	print "DEBUG: LOAD: Arrays erased\n" if $DEBUG;

	# Load Arrays
	# Seek to first ENTRY Mark. It should be right here, but you never know
	
	$line = $FILELINES[$CURRENT_LINE];
	$line =~ s /\n|\r//g;
	print "DEBUG: LOAD: First while: Data: $line, CURRENT_LINE: $CURRENT_LINE, TOTAL_LINE: $TOTAL_LINE\n" if $DEBUG;
	while ( (!($line =~ /^ENTRY:/)) && ($CURRENT_LINE <= $TOTAL_LINE) )
	{
		$CURRENT_LINE++;
		print "DEBUG: LOAD: Whoops... Advancing to next ENTRY.\n" if $DEBUG;
	} 

	print "DEBUG: LOAD: First if: CURRENT_LINE: $CURRENT_LINE, TOTAL_LINE: $TOTAL_LINE\n" if $DEBUG;
	if ($CURRENT_LINE >= $TOTAL_LINE)
	{
		print "DEBUG: LOAD: Read to end of file before ENTRY found\n" if $DEBUG;
	}
	else
	{	
		print "DEBUG: LOAD: Fount ENTRY. Advancing CURRENT_LINE.\n" if $DEBUG;
		$CURRENT_LINE++;
		$line = $FILELINES[$CURRENT_LINE];
		$line =~ s /\n|\r//g;
		print "DEBUG: LOAD: First second: Data: $line, CURRENT_LINE: $CURRENT_LINE, TOTAL_LINE: $TOTAL_LINE\n" if $DEBUG;
		while ( ($CURRENT_LINE <= $TOTAL_LINE) && (!($line =~ /^ENTRY:/)) )
		{
#			print "DEBUG: LOAD: In main loop\n" if $DEBUG;
	
			if ($line =~ /^VALUE:/)
			{
				$mini_index++;
				($void, $small_entry) = split (/:\s/, $line, 2);
				$small_entry =~ s/\n|\r//g;
				$FILES[$mini_index] = $small_entry;
				$FILESIZE[$mini_index] = "-";
			print "DEBUG: LOAD: small_entry: $small_entry\n" if $DEBUG;

				if (-f $small_entry)
				{
					$FILESTATUS[$mini_index] = "online"
				}
				else
				{
					$FILESTATUS[$mini_index] = "na";
				}
				print "DEBUG: LOAD: CURRENT_LINE: $CURRENT_LINE, Index: $mini_index, Filename: $small_entry\n" if $DEBUG; 
			}
			if ($line =~ /^SIZE:/)
			{
				($void, $small_entry) = split (/:/, $line, 2);
				$small_entry =~ s/\n|\r//g;
				$FILESIZE[$mini_index] = $small_entry;
				print "DEBUG: LOAD: CURRENT_LINE: $CURRENT_LINE, Index: $mini_index, Filesize: $small_entry\n" if $DEBUG; 
			}
			$CURRENT_LINE++;
			$line = $FILELINES[$CURRENT_LINE];
			$line =~ s /\n|\r//g;		
		}
	}
	$CURRENT_LINE = $original_current_line;
}

sub DO_DELETE
{
	my $arr_size;
	my ($single_status, $single_size, $single_file);
	my $junk_data;
	my $line;
	# We need a value to represent a new entry point into the LINES
	# Set this to true if this is the inital point into the routine
	# or if you previously deleted a file, and this is a new "position"
	# in LINES
	my $prev_delete_at_this_line = 1;
	
	# Refresh array total
	$TOTAL_LINE = @FILELINES;
	my $snap_current_line = $CURRENT_LINE;
	
	# We should be on an ENTRY marker, so let's advance to the virst VALUE marker
	$line = $FILELINES[$CURRENT_LINE];
	$line =~ s /\n|\r//g;
	while ( (!($line =~ /^VALUE:/)) && ($CURRENT_LINE <= $TOTAL_LINE) )
	{
		$CURRENT_LINE++;
		$line = $FILELINES[$CURRENT_LINE];
		$line =~ s /\n|\r//g;
	}
	print "DEBUG: DO_DELETE: Scanning to initial VALUE FILELINE:\n$line\n" if $DEBUG;
	
	while ($single_status = shift (@FILESTATUS) )
	{
		$single_size = shift (@FILESIZE);
		$single_file = shift (@FILES);
		
		if ($single_status =~ /^d/i)
		{
			if ($FILE_SAFE)
			{
				print "File safe is on. Not deleting $single_file\n";
			}
			else
			{
				unlink "$single_file";
			}
#			# Delete inital VALUE line
#			$line = $FILELINES[$CURRENT_LINE];
#			$line =~ s /\n|\r//g;
#			while ( (!($line =~ /^VALUE:/)) && ($CURRENT_LINE <= $TOTAL_LINE) )
#			{
#				$CURRENT_LINE++;
#				$line = $FILELINES[$CURRENT_LINE];
#				$line =~ s /\n|\r//g;
#			} 
#			$junk_data = splice (@FILELINES, $CURRENT_LINE, 1);
#			$junk_data =~ s/\n|\r//g;
#			$TOTAL_LINE = @FILELINES;
#			print "DEBUG: DO_DELETE: Inital line removed from FILELINES:\n$junk_data.\n$TOTAL_LINE lines left.\n" if $DEBUG;
#
#			# Delete other lines untill 
#			$line = $FILELINES[$CURRENT_LINE];
#			$line =~ s /\n|\r//g;
#			while ( (!($line =~ /^ENTRY:/))&&(!($line =~ /^TYPE:/))&&
#				(!($line =~ /^VALUE:/))&&(!($line =~ /^#/))&&
#				($CURRENT_LINE <= $TOTAL_LINE) )
#			{
#				$junk_data = splice (@FILELINES, $CURRENT_LINE, 1);
#				$junk_data =~ s/\n|\r//g;
#				$TOTAL_LINE = @FILELINES;
#				print "DEBUG: DO_DELETE: Line removed from FILELINES:\n$junk_data.\n$TOTAL_LINE lines left.\n" if $DEBUG;
#				$line = $FILELINES[$CURRENT_LINE];
#				$line =~ s /\n|\r//g;
#			}
#			
#			# Set a flag to let the next loop that the next VALUE line USED to
#			# be the home of a deleted value, but is no longer.
#			$prev_delete_at_this_line = 1;
		}
		else
		{
#			# File left intact. Goto next VALUE entry.
#			if ($prev_delete_at_this_line)
#			{
#				$line = $FILELINES[$CURRENT_LINE];
#				$line =~ s /\n|\r//g;
#				if ($line =~ /^VALUE:/)
#				{	
#					$CURRENT_LINE++;
#					$line = $FILELINES[$CURRENT_LINE];
#					$line =~ s /\n|\r//g;
#				}
#				$prev_delete_at_this_line = 0;
#			}
#			while ( (!($line =~ /^VALUE:/)) && ($CURRENT_LINE <= $TOTAL_LINE) )
#			{
#				$CURRENT_LINE++;
#				$line = $FILELINES[$CURRENT_LINE];
#				$line =~ s /\n|\r//g;
#				if ($line =~ /^ENTRY:/)
#				{
#					print "DEBUG: DO_DELETE: Whoah, went past where we were supposed to go FILELINE:\n$line.\n$TOTAL_LINE lines left.\n" if $DEBUG;
#					goto DAMAGECONTROL;
#				}
#			}
#			print "DEBUG: DO_DELETE: Scanning to next VALUE FILELINE:\n$line.\n$TOTAL_LINE lines left.\n" if $DEBUG;
#
		}
#		if ($CURRENT_LINE >= $TOTAL_LINE)
#		{
#			die ("Tried to read past end of file during DO_DELETE scan\n");
#		}
	}
DAMAGECONTROL:
	# These should be empty, but just in case ...
	#&ERASE_ARRAY(\@FILES);
	#&ERASE_ARRAY(\@FILESTATUS);
	#&ERASE_ARRAY(\@FILESIZE);
	$CURRENT_LINE = $snap_current_line;
	$STATUS = "Delete completed";
}


sub PRINT_BUFFER
{
	my $mini_index;
	my $mini_total = @FILES;
	my ($temp_file, $temp_size, $temp_status);
	
	if ($mini_total == 0)
	{
		print "No files in buffer...\n\n";
	}
	else
	{
		print "DEBUG: PRINT_BUFFER: $mini_total entries in buffer\n" if $DEBUG;
		#       01234567890123456789012345678901234567890123456789012345678901234567890123456789
		printf "NO  STATUS     SIZE         FILENAME\n";
		print "\n";
#		printf "______________________________________________________________________\n";
		
		for ($mini_index = 0; $mini_index < $mini_total; $mini_index++)
		{
			$temp_status = $FILESTATUS[$mini_index];
			$temp_size = $FILESIZE[$mini_index];
			$temp_file = $FILES[$mini_index];
			printf "%-4d%-10s%-12d%-50s\n\n", $mini_index, $temp_status, $temp_size, $temp_file;

		}
	}
	print "\n"; 	
}

sub SET_DELETE
{
	my $request = $_[0];
	my @file_numbers;
	my $items;
	
	$request =~ s/\n|\r//g;
	$request =~ s/^d(.*)/$1/i;
	$request =~ s/^\s//g;
	print "DEBUG: SET_DELETE: request is $request\n" if $DEBUG;
	@file_numbers = split(/\s/,$request);
	
	if ($request =~ /[A-Z,a-z]/)
	{
		$STATUS = "Bad delete syntax";
	}
	else
	{
		$items = @file_numbers;
		print "DEBUG: SET_DELETE: Found $items requests for delete\n" if $DEBUG;
		while ($items > 0)
		{
			$request = shift(@file_numbers);
			print "DEBUG: SET_DELETE: Request to delete $request\n" if $DEBUG;
	
			if (defined($FILESTATUS[$request]))
			{
				$FILESTATUS[$request] = "delete";
				print "DEBUG: SET_DELETE: Setting delete flag on $request\n" if $DEBUG;
				$STATUS = "File(s) set for deletion. Use C to delete. See above.";
			}
			else
			{
				print "DEBUG: SET_DELETE: request is $request\n" if $DEBUG;
				$STATUS = "File number not found.";
			}
			$items = @file_numbers;
		}
	}
}

sub SET_KEEP
{
	my $request = $_[0];
	my @file_numbers;
	my $items;
	my $total_items;
	my $count;
	
	$request =~ s/\n|\r//g;
	$request =~ s/^k(.*)/$1/i;
	$request =~ s/^\s//g;
	print "DEBUG: SET_KEEP: request is $request\n" if $DEBUG;
	@file_numbers = split(/\s/,$request);
	
	if ($request =~ /[A-Z,a-z]/)
	{
		$STATUS = "Bad keep syntax";
	}
	else
	{
		# Set them all to delete initally
		$total_items = @FILESTATUS;
		for ($count = 0; $count < $total_items; $count++)
		{
			if ($FILESTATUS[$count] =~ /keep/)
			{
				# Keep the keep
			}
			else
			{
				$FILESTATUS[$count] = "delete";
			}
		}
		
		$items = @file_numbers;
		print "DEBUG: SET_KEEP: Found $items requests for keep\n" if $DEBUG;
		
		while ($items > 0)
		{
			$request = shift(@file_numbers);
			print "DEBUG: SET_KEEP: Request to keep $request\n" if $DEBUG;
			if (defined($FILESTATUS[$request]))
			{
				$FILESTATUS[$request] = "keep";
				print "DEBUG: SET_KEEP: Setting keep flag on $request\n" if $DEBUG;
				$STATUS = "File(s) set for deletion. Use C to delete. See above.";
			}
			else
			{
				print "DEBUG: SET_KEEP: request is $request\n" if $DEBUG;
				$STATUS = "File number not found.";
			}
			$items = @file_numbers;
		}
	}
}


sub SAVE_BACK
{
	my $fname;
	my $temp_counter = 0;
	
	$TOTAL_LINE = @FILELINES;
	
	print "\n\n";
	print "Please enter the full path of the log file:\n";
	$fname = &GET_RESPONSE;
	$fname =~ s/\\/\//g;
	if ((-e $fname))
	{
		print "\nUnable to save logfile. File exists.\n";
		$STATUS = "Unable to savelogfile. Using logfile exists.";
		&PAUSE;
		goto END;
	}
	else
	{
		open (REPORT, ">$fname");
		while ($temp_counter <= $TOTAL_LINE)
		{
			print REPORT $FILELINES[$temp_counter];
			print REPORT "\n";
			$temp_counter++;
		}
		close (REPORT);
		$STATUS = "Logfile saved to $fname";
	}
}

&INIT_PROG;			# Initalize all the stuff



while (!$QUITTING)
{
	my $response;


	&SPLAT();
	&PRINT_BUFFER;
	&DISPLAY_PANEL;
	
	$response = &GET_RESPONSE;
	if ($response =~ /^debug\b/i)
	{
		$DEBUG = (!($DEBUG));
		if (!defined($DEBUG))
		{
			$DEBUG = "0";
		}
		$STATUS = "Debug toggled to $DEBUG"
	}
	elsif ($response =~ /^n\b/i)
	{	# Goto next key and load
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(1);
		&LOAD;
			
	}	
	elsif ($response =~ /^nn\b/i)
	{	# Goto next key and load
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(10);
		&LOAD;
	}
	elsif ($response =~ /^nnn\b/i)
	{	# Goto next key and load
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(100);
		&LOAD;
	}
	elsif ($response =~ /^m\b/i)
	{	# Goto previous key and load
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(-1);
		&LOAD;
	}
	elsif ($response =~ /^mm\b/i)
	{	# Goto previous key and load
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(-10);
		&LOAD;
	}
	elsif ($response =~ /^mmm\b/i)
	{	# Goto previous key and load
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(-100);
		&LOAD;
	}
	elsif ($response =~ /^t/i)
	{	# Goto next test block
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK('f');
		&LOCK(1);	# Rule: Must end on a ENTRY line
		&LOAD;
	}
	elsif ($response =~ /^r/i)
	{	# Goto previous test block
#		if (!($CONFIRMATION))
#		{
#			&DO_DELETE;
#		}
		&LOCK(-1);	# Bump us just before the previous TYPE:
		&LOCK('b');
		&LOCK(1);	# Rule: Must end on a ENTRY line
		&LOAD;
	}
	elsif ($response =~ /^f/i)
	{	#read input file
		&SET_INFILE();
		$STATUS = $STATUS;
	}
	elsif ($response =~ /^d/i)
	{	#set delete flag on file(s)
		&SET_DELETE($response);
	}
	elsif ($response =~ /^k/i)
	{	#keep one and set delete flag on the other(s)
		&SET_KEEP($response);
	}
	elsif ($response =~ /^c/i)
	{	#quitting
		&DO_DELETE;
	}
	elsif ($response =~ /^s/i)
	{	#flush the FILELINE buffer to a new file
		&SAVE_BACK;
	}
	elsif ($response =~ /^q/i)
	{	#quitting
		$QUITTING = 1;
	}	

}

die ("Later.\n");
