#! /usr/bin/perl -w
########################################################################
#
#	Duplicate file checker Version 3.1
#
#	Creates a checksum and name database for a set of perticular
#	filesystems and checks for the commanalities between them
#
#	By: Chris McCluskey	Current Date: 20020723
#
########################################################################
# 
# HISTORY:
# pre 20020723
#	Orginally used DBM,    but this became clunky due to poor implementation 
#	in non-UNIX system (no support for data values larger than 1024B. Incremented
#	verison counter to 3.1 to represent the shift to MySQL.
#
# TODO:
# 20020804	Rewrite -(#) cases in addition to the (#) series to NULL
# ?. Add strict command line variables
# ?. Check the validy of typed in check types
# ?. List the current DBs avalible on the hd
# ?. Progress meter
# ?. Come up with new ativity indicator (dots are not clear enough)
# ?. Make remove DB by a listed number  ex. 1. DATABASE, >>> 1
########################################################################

use strict;		# Strict type variable checking
use Cwd;		# Used in finding working dir in ADDFILES
use DBI;		# Database Independant routines for queries
			# to MySQL
			
###############################

my $DBHOST = "192.168.1.101";	# Hostname of the MySQL Database
my $DBPORT = "3306";		# SQL port
my $DBUSER = "dupuser";		# User who had necessary access to database $DBNAME
my $DBPASS = "duppass";		# Password for above user
my $DBNAME = "dupdb";		# Database name
my $DUPTBL = "duptable";	# Primary table
my $DBIARGS = "";	# Special arguments passed to DBI
###############################

my $KEEP_SUFFIX = 0;	# Check the suffix when comparing filenames
my $DASH_TO_UNDERS = 1;	# Treat dashes and underscores as the same char
my $OS='win';		# What OS is this for (implemeted mac/unix/win)
my $CKSUM_TYPE = 'md5';	# Use md5 or sysV checksums

###############################

#my $INDEX = 0;
my $DEBUG = 1;
my $REPORT_FILE = undef;	# Init that report is not sent to disk
					# Set varible to send report file to disk
#my @REPORT_TYPES = ('checksum','name');	# What type of checks are available
my @REPORT_TYPE = ('checksum','name','partchecksum');	# What type of checks need to be run
my $INCLUDE_SIZE = 1;	# Include file size information in report


# ??? What are these?
my (%DBS, $dbname);

my ($BASE_DIR, $DIRSEP, $ENTRYSEP, $DB_DIR, $TEMP_DIR);
if ($OS eq 'mac')
{ 
	# You'll probably need to change $BASE_DIR
	$BASE_DIR = 'Hard Drive'; $DIRSEP = ':'; $ENTRYSEP='::';
	$DB_DIR = "$BASE_DIR".".imgfiles"; # Directory containing the FileDBs
	$TEMP_DIR = getcwd();
}
elsif ($OS eq 'unix')
{ 
	$BASE_DIR = '/'; $DIRSEP = '/'; $ENTRYSEP = '/'; 
	$DB_DIR = "$BASE_DIR"."root$DIRSEP".".imgfiles"; # Directory containing the FileDBs
	$TEMP_DIR = getcwd();
}
elsif ($OS eq 'win')
{
	# You'll probably need to change $BASE_DIR
	$BASE_DIR = 'c:/'; $DIRSEP = '/'; $ENTRYSEP = '/'; 
	$DB_DIR = "$BASE_DIR".".imgfiles"; # Directory containing the FileDBs
	$TEMP_DIR = "$BASE_DIR".".tempfiles"; # Directory containing the temporary entries used in processing
}
else
{
	$BASE_DIR = '/';
	$DIRSEP = '/';		# The directory item speartor for platform used
	$DB_DIR = "$BASE_DIR".".imgfiles"; # Directory containing the FileDBs
	$TEMP_DIR = getcwd();
}

if ($CKSUM_TYPE =~ /md5/)
{
	use Digest::MD5;
}

my $VERSION = '3.1';
my $QUITTING = 0;
my $SIZE_EXTN = 'size';
my $NAME_EXTN = 'name';
my $CKSUM_EXTN = 'cksum';
my $SIZEDB_NAME = "$TEMP_DIR$DIRSEP"."temp.$SIZE_EXTN";
my $NAMEDB_NAME = "$TEMP_DIR$DIRSEP"."temp.$NAME_EXTN";
my $CKSUMDB_NAME = "$TEMP_DIR$DIRSEP"."temp.$CKSUM_EXTN";
#my $ENTRYSEP = '>-<';
my $MARKERSEP = '><';
my $DBM_EXTN = '.pag';
my $DELIM = "\t";
my $DSEXTN = ".tag";
my @files;	# Array of file names
########################################################################

&INIT_DB;			# Initalize all the stuff and delete stale files 

while (!$QUITTING)
{
	my $response;

	&DISPLAY_MENU;
	$response = &GET_RESPONSE;
	if ($response =~ /^c/i)
	{	#create database
		&MK_DB;
	}
	elsif ($response =~ /^l/i)
	{	#load database
		&ADD_DB;
	}
	elsif ($response =~ /^r/i)
	{	#remove database
		&REM_DB;
	}
	elsif ($response =~ /^p/i)
	{	#process database
		
#		if ($OS eq 'win')
#		{
#			&PROCESS_DBMLESS;
#		}
#		else
#		{
			&PROCESS;
#		}
	}
	elsif ($response =~ /^t/i)
	{	#types of checks to be done
		&SET_CHECKTYPE;
	}
	elsif ($response =~ /^f/i)
	{	#filename of the output file
		&SET_OFILENAME;
	}
	elsif ($response =~ /^s/i)
	{	#sizes in report
		if ($INCLUDE_SIZE == 1)
		{
			$INCLUDE_SIZE = 0;
		}
		else
		{
			$INCLUDE_SIZE = 1;
		}
	}
	elsif ($response =~ /^q/i)
	{	#quitting
		$QUITTING = 1;
	}
	elsif ($response =~ /^d/i)
	{
		&DEL_DB;
	}
	else
	{
		&DISPLAY_MENU;
	}
}

&INIT_DB;
die ("Later.\n");


sub INIT_DB
{
	my $temp_fname;

	if (!(-d $TEMP_DIR))
	{
		print "DEBUG: Creating temporary directory $TEMP_DIR\n" if $DEBUG;
		mkdir($TEMP_DIR,0770) || die("Could not create directory ($TEMP_DIR) for the temp files. Please modify the the DB_DIR variable or create the directory tree manually.\n");
	}
	if (!(-d $DB_DIR))
	{
		print "DEBUG: Creating DB tabs directory $DB_DIR\n" if $DEBUG;
		mkdir($DB_DIR,0770) || die("Could not create directory ($DB_DIR) for the database files. Please modify the the DB_DIR variable or create the directory tree manually.\n");
	}
	
	my $dbhandle;
	$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",
		$DBUSER,$DBPASS,$DBIARGS);
	if (!($dbhandle))
	{
		&DEAD_JIM;
	}
	
	my $count;
	$count = $dbhandle->selectrow_array ("SELECT COUNT(*) FROM $DUPTBL");
	print "DEBUG: Database $DBNAME online with $count rows.\n" if $DEBUG;
	
	$dbhandle->disconnect ();
}

sub DISPLAY_MENU
{
	print <<"EOF";


Duplicate File Checker                       Version: $VERSION
By: Chris McCluskey

EOF
	print "OPTIONS:\n";
#####
	
	# Find the distinct dataset tags already loaded into the database
	my $dbhandle;
	$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",
			$DBUSER,$DBPASS,$DBIARGS);
	if (!($dbhandle)) { &DEAD_JIM; }
		
	my $queryhandle;
	$queryhandle = $dbhandle->prepare ("SELECT DISTINCT dataset FROM $DUPTBL");
	$queryhandle->execute();
	
	my $any_dbs = 0;
	my $dsvalue;
	my @dsvalues;
	while (my @value = $queryhandle->fetchrow_array() )
	{
		$dsvalue = $value[0];
		$dsvalue =~ s/\s//g;
		unshift (@dsvalues,$dsvalue);
		$any_dbs++;
#		print "$any_dbs ";
	}
	$dbhandle->disconnect ();

	print "\tDatabases for checking: ";	
	if ($any_dbs)
	{
		while ($dsvalue = shift(@dsvalues) )
		{
			print "$dsvalue ";
		}
	}
	else
	{
		print "-none-";
	}			
	print "\n";
#####	

	my ($no_types, $count);
	print "\tTypes of checks that will be completed: ";
	$no_types = @REPORT_TYPE;
	if ($no_types == 0)
	{
		print "-none-\n";
	}
	else
	{
		for ($count = 0; $count < $no_types; $count++)
		{
			$_ = $REPORT_TYPE[$count];
			print "$_ ";
		}
		print "\n";
	}
#####	
	
	print "\tReport filename: ";
	if (!$REPORT_FILE)
	{
		print " -none-  Report to Standard Output only.\n";
	}
	else
	{
		print "$REPORT_FILE\n";
	}
#####	
	
	if ($INCLUDE_SIZE)
	{
		print "\tSizes will be included in report.\n";
	}
	else
	{
		print "\tSizes will not be included in report.\n";
	}
	print "\n";

	print <<"EOF";
C ..... Create a filesystem database
L ..... Load a previously created filesystem database for processing
R ..... Remove a filesystem database out of the queue for processing
D ..... Delete a filesystem database from the hard drive

P ..... Process the current filesystem databases in the queue

T ..... Type of checks to do (Name checks, Checksum checks)
F ..... Set the filename of the report file
S ..... Include/exclude the size of the files in the report

Q ..... Quit

EOF
	print ">>>";
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

sub ADD_DB
{
	my ($fname,$fname_long);

	$fname = $_[0];

	if (!(defined($fname) ))
	{
		print "\nPlease enter the filename of the file database you want loaded: ";
		$fname = &GET_RESPONSE;
	}
	if (-e $fname)
	{
		$fname_long = $fname;
	}
	elsif (-e "$fname$DSEXTN")
	{
		$fname_long = "$fname$DSEXTN";
	}
	else
	{
		$fname_long = "$DB_DIR$DIRSEP$fname";
		$fname_long =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
		if (!(-e $fname_long))
		{
			$fname_long = "$fname_long$DSEXTN";
		}
	}
	
	print ("DEBUG: ADD_DB: Using filename $fname_long\n") if $DEBUG;
	
	if (-e $fname_long)
	{
		my $dataline;
		my ($fullfilename,$rootpath,$filename,$size,$checksumtype,$checksum,$partchecksum);
		my ($host,$dataset);
		my $keyfilename;
		
		open (DATASET, $fname_long) || die ("Unable to load dataset file $fname_long for loading into database");
		binmode DATASET;
		
		# Open DB connection
		my ($dbhandle,$queryhandle,$rows);
		$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",
			$DBUSER,$DBPASS,$DBIARGS);
		if (!($dbhandle)) { &DEAD_JIM; }
		
		my @linearr;
		my $entcount;
		while ($dataline = <DATASET>)
		{
			if ($dataline =~ /.*\n.*\n.*/)
			{
				@linearr = split("\n", $dataline);
				$entcount = @linearr;
				print "DEBUG: ADD_DB: Multiple records found in dataline. Found $entcount records.\n" if $DEBUG;
				$dataline = shift(@linearr);		
			}
ANOTHERRECORD:
			if ($dataline =~ /^#/)
			{
				print "DEBUG: Found comment in dataset file: $dataline\n" if $DEBUG;
			}
			else
			{
				($fullfilename,$rootpath,$filename,$size,$checksumtype,$checksum,$partchecksum,
						$host,$dataset) = split ($DELIM, $dataline);

				print "DEBUG: Imported values check:\n" if $DEBUG;			
				print "fullfilename:\t$fullfilename\nrootpath:\t$rootpath\nfilename:\t$filename\n" if $DEBUG;
				print "size:\t$size\nchecksumtype:\t$checksumtype\nchecksum:\t$checksum\n" if $DEBUG;
				print "partchecksum:\t$partchecksum\nhost:\t$host\ndataset:\t$dataset\n" if $DEBUG;	
	
				$keyfilename = &DO_KEY($fullfilename);
				# Check to see if data is already there
				$queryhandle = $dbhandle->
					prepare ("SELECT fullfilename, filename, dataset FROM $DUPTBL WHERE fullfilename=? AND filename=? AND dataset=?");
				$queryhandle->execute($fullfilename ,$keyfilename ,$dataset);
				$rows = $queryhandle->fetchrow_arrayref();
				if (defined($rows->[0]))
				{
					print "DEBUG: Data aleady in database: fillfilename: $fullfilename, filename: $keyfilename, dataset: $dataset\n" if $DEBUG;
				}
				else
				{
					# ... not there so insert row
					$rows = $dbhandle->
						do ("INSERT INTO $DUPTBL (fullfilename,rootpath,filename,size,checksumtype,checksum,partchecksum,dataset) VALUES (?,?,?,?,?,?,?,?)", undef, $fullfilename, $rootpath, $keyfilename, $size, $checksumtype, $checksum,$partchecksum, $dataset);
					if (!(defined($rows)))
					{
						die ("Failed INSERT into database");
					}
					else
					{
						print "DEBUG: $rows rows inserted for keyed entry\n";
					}
				}	
			}
			# Are there still remaining entries in the file array
			if ($dataline = shift(@linearr))
			{
				goto ANOTHERRECORD;
			}
		}
		$dbhandle->disconnect ();
		close (DATASET);
	}
	else
	{
		print "\nFile dataset not found. Please check the ";
		print "filname and try again.\n";
		&PAUSE;
	}
}

sub REM_DB
{
	my ($keytemp, $name);

	print "\n\nThe current databases in the queue are: ";

	# Find the distinct dataset tags already loaded into the database
	my $dbhandle;
	$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",
			$DBUSER,$DBPASS,$DBIARGS);
	if (!($dbhandle)) { &DEAD_JIM; }
		
	my $queryhandle;
	$queryhandle = $dbhandle->prepare ("SELECT DISTINCT dataset FROM $DUPTBL");
	$queryhandle->execute();
	
	my $any_dbs = 0;
	my $dsvalue;
	my @dsvalues;
	while (my @value = $queryhandle->fetchrow_array() )
	{
		$dsvalue = $value[0];
		$dsvalue =~ s/\s//g;
		unshift (@dsvalues,$dsvalue);
		$any_dbs++;
#		print "$any_dbs ";
	}
	$queryhandle->finish();
	$dbhandle->disconnect ();

	if ($any_dbs)
	{
		while ($dsvalue = shift(@dsvalues) )
		{
			print "$dsvalue ";
		}
	}
	else
	{
		print "-none-";
	}			
	print "\n";

	if ($any_dbs)
	{
		print "Please enter the database you want removed (to cancel please press ENTER): ";
		$name = &GET_RESPONSE;
		$name =~ tr/[a-z]/[A-Z]/;
		$name =~ s/\s//g;
		

		# Open DB connection
		my ($dbhandle,$queryhandle,$rows);
		$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",
			$DBUSER,$DBPASS,$DBIARGS);
		if (!($dbhandle)) { &DEAD_JIM; }

		# Check to see if data is already there
		$queryhandle = $dbhandle->
			prepare ("SELECT dataset FROM $DUPTBL WHERE dataset=\"$name\"");
		$queryhandle->execute();
		$rows = $queryhandle->fetchrow_arrayref();
		if (defined($rows->[0]))
		{
			# Let's do some deletes
			$rows = $dbhandle->
				do ("DELETE FROM $DUPTBL WHERE dataset =\"$name\"");
			if (!(defined($rows)))
			{
				die ("Failed DELETE from database");
			}
			else
			{
				print "DEBUG: $rows rows deleted\n";
			}
		}
		else
		{
			print "There are no datasets $name in the database... Press enter to continue.\n";
			&PAUSE;
		}
		$queryhandle->finish();
		$dbhandle->disconnect ();		
	}
	else
	{
		print "There are no datasets currently in queue... Press enter to continue.\n";
		&PAUSE;
	}
}

sub DEL_DB
{
	my ($resp,$keytemp, $name);

	print "Please enter the name of the database set you want removed: ";
	$name = &GET_RESPONSE;
#	if ($DBS{$name})
#	{
#		print "This set is in the queue for processing. ";
#		print "Delete anyway and remove from queue? (Y/N) ";
#		$resp = &GET_RESPONSE;
#		if ($resp =~ /^y/i)
#		{
#			delete $DBS{$name};
#		}
#		else
#		{
#			goto DEL_DBEND;
#		}
#	}
#	$name = "$DB_DIR$DIRSEP$name";
#	$name =~ s/$DIRSEP$DIRSEP//;
	print "These are the files that will be removed:\n";
	while (<$name.*>)
	{
		
		if (-d $name)
		{
			print "Excluded: $_\n" if $DEBUG;
		}
		else
		{
			print "$_\n";
		}	
	}
	print "Confirm deletion of these files? (Y/N) ";
	$resp = &GET_RESPONSE;
	if ($resp =~ /^y/i)
	{
		while (<$name.*>)
		{
			if (-d $name)
			{
				print "Excluded: $_\n" if $DEBUG;
			}
			else
			{
				print "Removing file: $_\n";
				unlink ($_) || print "Error: Unable to unlink $_\n";
			}
		}
	}	
	else
	{
		print "Deletion cancelled.\n"
	}
	print "Deletion complete... Press ENTER.\n";
	&PAUSE;
DEL_DBEND:
}

sub SET_OFILENAME
{
	my $fname;

	print "\n\n";
	print "Please enter the full path of the report file (if the file";
	print " exists, it will be appended):\n";
	$fname = &GET_RESPONSE;
	open (REPORT, ">>$fname");
	if (!(-e $fname))
	{
		print "\nUnable to open or create the output report file.\n";
		&PAUSE;
	}
	else
	{
		$REPORT_FILE = $fname;
	}
	close (REPORT);
	return (0);
}

sub PAUSE
{
	&GET_RESPONSE();
}

sub SET_CHECKTYPE
{
	my ($types,@report_type_temp,$numtypes, $count);

	print "Please type out the name of each search routines you wish to apply ";
	print "to the file system databases. Type in lower case and with a space ";
	print "between the name of each routine, ";
	print "in the order you wish them applied.";
	print "\n\nFor example if you wanted to execute a ";
	print "checksum search followed by a name search please type:\n";
	print "checksum name\n\n";
	print "The following search routines are available: ";
	
	$numtypes = @REPORT_TYPE;
	if ($numtypes == 0)
	{
		print "-none-\n";
	}
	else
	{
		for ($count = 0; $count < $numtypes; $count++)
		{
			$_ = $REPORT_TYPE[$count];
			print "$_ ";
		}
		print "\n";
	}
	
	print "\nPlease enter the methods now: ";
	$types = <STDIN>;
	chop($types);
	@report_type_temp = split(/ /,$types);
	#do additional error checking here
	@REPORT_TYPE = @report_type_temp;
	return (0);
}

sub MK_DB
{
	my ($fname,$fname_long, $full_path, $trunc_path);
	my ($dentry, $dentry_short, $addto, $item_count);

	print "\nPlease enter the filename you wish to use for the new dataset ";
	print "(the file containing the file characteristcs): ";
	$fname = &GET_RESPONSE;
	$fname =~ s/\\/\//g;
	$fname =~ tr/[a-z]/[A-Z]/;
	if ($fname =~ /$DIRSEP/)
	{
		$fname_long = $fname;
		$fname =~ s/.*$DIRSEP(\S*)\B/$1/;
	}
	$fname_long = "$DB_DIR$DIRSEP$fname$DSEXTN";
	$fname_long =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	if (-e "$fname_long")
	{
		print "\nI'm sorry but a dataset using that name ";
		print "already exists.\n";
		&PAUSE;
		goto END;
	}

	print "Please enter the full path of the directory you wish ";
	print "to create the database of: ";
	$full_path = &GET_RESPONSE;
	$full_path =~ s/\\/\//g;
	if (!(-e $full_path))
	{
		print "\nSorry, but that path does not exist. Please make sure ";
		print "that such a directory is mounted.\n";
		&PAUSE;
		goto END;
	}
	if ($OS ne 'mac')
	{
		print <<"EOF";

Next, the leading directory information (the mount point) must be 
truncated from the full filename. For example, we want to catalog the 
files on a CD-ROM mounted on /mnt/cdrom. The normal path to the file 
foo.bar would be /mnt/cdrom/foo.bar. However, /mnt/cdrom is not part of 
the CD-ROM filesystem. In this case the truncated portion of the file 
name would be /mnt/cdrom (or /mnt/cdrom/). If you wish to keep the 
current full path for the filesystem simply press ENTER at the prompt 
(keep in mind though that this mount point may change at a later date 
invalidating the database information).

EOF
		if ($OS =~ /win/)
		{
			print "Windows users typically will want to press ENTER here\n\n";
		}
		print "Please type out the path you wish to truncate: ";
		$trunc_path = &GET_RESPONSE;
		$trunc_path =~ s/\\/\//g;
		if (($trunc_path) && (!($full_path =~ /$trunc_path/i)))
		{
			print "\nThe path you wish to truncate ($trunc_path) ";
			print "is not contained within the full path ";
			print "($full_path). Please try again.\n\n";
			&PAUSE;
			goto END;	
		}
	}

	&ADDFILES($full_path, 0);	# Construct the file list array
	$item_count = @files;
	print "DEBUG: Number of files found: $item_count\n" if $DEBUG;
	
	open (DATASET, ">$fname_long") || die ("Couldn't open $fname_long for writing.");
	print "DEBUG: Dataset file $fname_long opened for writing\n" if $DEBUG;
	
	my $date = &GET_TIME;
	# Print header
	print DATASET "# DATASET: $fname\n";
	print DATASET "# DATE: $date\n";
	print DATASET "#\n";
	print DATASET "# FORMAT: fullfilename$DELIM";
	print DATASET "rootpath$DELIM";
	print DATASET "filename$DELIM";
	print DATASET "size$DELIM";
	print DATASET "checksumtype$DELIM";
	print DATASET "checksum$DELIM";
	print DATASET "partchecksum$DELIM";
	print DATASET "host$DELIM";
	print DATASET "dataset\n";
	
	my $item_current = 0;
	while ($dentry = (shift(@files)))
	{
		my ($fullfilename,$rootpath,$filename,$size,$checksumtype);
		my ($checksum,$partchecksum,$host,$dataset);

		print "DEBUG: Current dentry is $dentry\n";
		$dentry_short = $dentry;
		print "DEBUG: Dentry rewrite: $dentry_short\n" if $DEBUG;
		$dentry_short =~ s/(.*)$DIRSEP(.*)\b/$2/;
		print "DEBUG: Dentry rewrite: $dentry_short\n" if $DEBUG;

		
#		if ($OS =~ /unix/)
#		{
#			while ($dentry_short =~ /^$DIRSEP/)
#			{
#				$dentry_short =~ s/$DIRSEP//;
#			}
#		}
		$fullfilename = $dentry;
		$rootpath = $trunc_path;
		$filename = $dentry_short;
		$size = &DO_SIZE($dentry);
		$checksumtype = $CKSUM_TYPE;
		$checksum = &DO_CKSUM($dentry);
		$partchecksum = &DO_PARTCKSUM($dentry);
		$host = '';
		$dataset = $fname;
		
		print DATASET "$fullfilename$DELIM$rootpath$DELIM$filename$DELIM$size$DELIM";
		print DATASET "$checksumtype$DELIM$checksum$DELIM$partchecksum$DELIM";
		print DATASET "$host$DELIM$dataset\n";
		
		print "fullfilename:\t$fullfilename\nrootpath:\t$rootpath\nfilename:\t$filename\n" if $DEBUG;
		print "size:\t$size\nchecksumtype:\t$checksumtype\nchecksum:\t$checksum\n" if $DEBUG;
		print "partchecksum:\t$partchecksum\nhost:\t$host\ndataset:\t$dataset\n" if $DEBUG;


		$item_current++;
		if (!($item_current % 10))
		{
			print "$item_current ";
			print "\n" if $DEBUG;
		}
	}
	close (DATASET);

	print "\nDo you wish to add this database to the processing queue ";
	print "for later processing? (Y/N) ";
	$addto = &GET_RESPONSE();
	if ($addto =~ /^y/i)
	{
		&ADD_DB($fname);
	}
END:	
}

sub PROCESS
{
	my (@entries,$key_temp,$key_value);
	my ($dbname,$fullname,$file_entry,$new_index,$rep_type);
	my (%name,$cksum,%size,%nametemp,%cksum,%sizetemp,%cksumtemp);
	my (@REPORT_TYPE_POPPED);

	@REPORT_TYPE_POPPED = @REPORT_TYPE;
	while ($rep_type=shift(@REPORT_TYPE_POPPED))
	{
		if ($rep_type =~ /^checksum/i)
		{
			&PROCESS_CHECKSUM;
		}
		elsif ($rep_type =~ /^name/i)
		{
			&PROCESS_NAME;
		}
		elsif ($rep_type =~ /^partchecksum/i)
		{
			&PROCESS_PARTCHECKSUM;
		}
		else
		{
			print "Error. No such search type available.\n";
		}
	}
}

sub PROCESS_CHECKSUM
{
	if ($REPORT_FILE)
	{
		if (-e $REPORT_FILE)
		{
			print "Appending report file...\n";
		}
		else
		{
			print "Creating report file...\n";
		}
		open (REPORT, ">>$REPORT_FILE") || die ("Unable to open report file.\n");
	}
	print "Checksum checks...\n\n";
	print REPORT "TYPE:checksum\n";
	print REPORT "#\n";
	
	my $dbhandle;
	$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",$DBUSER,$DBPASS,$DBIARGS);
	if (!($dbhandle)) { &DEAD_JIM; }

	my $queryhandle;
	$queryhandle = $dbhandle->prepare ("SELECT DISTINCT checksum FROM $DUPTBL");
	$queryhandle->execute();
	
	my $rows = 0;
	my $cksumvalue;
	my @cksumvalues;
	while (my @value = $queryhandle->fetchrow_array() )
	{
		$cksumvalue = $value[0];
		$cksumvalue =~ s/\s//g;
		unshift (@cksumvalues,$cksumvalue);
		$rows++;
	}
	$queryhandle->finish();
	print "DEBUG: PROCESS_CHECKSUM: $rows unique checksums found\n" if $DEBUG;

	while ($cksumvalue = shift(@cksumvalues))
	{
		my $count;
		$count = $dbhandle->selectrow_array ("SELECT COUNT(*) FROM $DUPTBL WHERE checksum=?", undef, $cksumvalue);
		if ($count > 1)
		{
			print REPORT "ENTRY:$cksumvalue\n";
			print "ENTRY:$cksumvalue\n" if $DEBUG;
			
			$queryhandle = $dbhandle->
				prepare ("SELECT fullfilename,size FROM $DUPTBL WHERE checksum=?");
			$queryhandle->execute($cksumvalue);
			while ($rows = $queryhandle->fetchrow_arrayref())
			{
				if (-e $REPORT_FILE)
				{
					print REPORT "VALUE: $rows->[0]\n";
					print REPORT "SIZE: $rows->[1]\n" if $INCLUDE_SIZE;
				}
				else
				{
					print "VALUE: $rows->[0]\n";
					print "SIZE: $rows->[1]\n";
				}
				print "VALUE: $rows->[0]\n" if $DEBUG;
				print "SIZE: $rows->[1]\n" if $DEBUG;
			}
			$queryhandle->finish();
			print REPORT "#\n";
		}
	}	

	$dbhandle->disconnect ();
	
	print "#\n";
	close (REPORT);
}

sub PROCESS_PARTCHECKSUM
{
	if ($REPORT_FILE)
	{
		if (-e $REPORT_FILE)
		{
			print "Appending report file...\n";
		}
		else
		{
			print "Creating report file...\n";
		}
		open (REPORT, ">>$REPORT_FILE") || die ("Unable to open report file.\n");
	}
	print "Partial checksum checks...\n\n";
	print REPORT "TYPE:partchecksum\n";
	print REPORT "#\n";
	
	my $dbhandle;
	$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",$DBUSER,$DBPASS,$DBIARGS);
	if (!($dbhandle)) { &DEAD_JIM; }

	my $queryhandle;
	$queryhandle = $dbhandle->prepare ("SELECT DISTINCT partchecksum FROM $DUPTBL");
	$queryhandle->execute();
	
	my $rows = 0;
	my $cksumvalue;
	my @cksumvalues;
	while (my @value = $queryhandle->fetchrow_array() )
	{
		$cksumvalue = $value[0];
		$cksumvalue =~ s/\s//g;
		unshift (@cksumvalues,$cksumvalue);
		$rows++;
	}
	$queryhandle->finish();
	print "DEBUG: PROCESS_PARTCHECKSUM: $rows unique partial checksums found\n" if $DEBUG;

	while ($cksumvalue = shift(@cksumvalues))
	{
		my $count;
		$count = $dbhandle->selectrow_array ("SELECT COUNT(*) FROM $DUPTBL WHERE partchecksum=?", undef, $cksumvalue);
		if ($count > 1)
		{
			print REPORT "ENTRY:$cksumvalue\n";
			print "ENTRY:$cksumvalue\n" if $DEBUG;
			
			$queryhandle = $dbhandle->
				prepare ("SELECT fullfilename,size FROM $DUPTBL WHERE partchecksum=?");
			$queryhandle->execute($cksumvalue);
			while ($rows = $queryhandle->fetchrow_arrayref())
			{
				if (-e $REPORT_FILE)
				{
					print REPORT "VALUE: $rows->[0]\n";
					print REPORT "SIZE: $rows->[1]\n" if $INCLUDE_SIZE;
				}
				else
				{
					print "VALUE: $rows->[0]\n";
					print "SIZE: $rows->[1]\n";
				}
				print "VALUE: $rows->[0]\n" if $DEBUG;
				print "SIZE: $rows->[1]\n" if $DEBUG;
			}
			$queryhandle->finish();
			print REPORT "#\n";
		}
	}	

	$dbhandle->disconnect ();
	
	print "#\n";
	close (REPORT);
}

sub PROCESS_NAME
{
	if ($REPORT_FILE)
	{
		if (-e $REPORT_FILE)
		{
			print "Appending report file...\n";
		}
		else
		{
			print "Creating report file...\n";
		}
		open (REPORT, ">>$REPORT_FILE") || die ("Unable to open report file.\n");
	}
	print "Name checks...\n\n";
	print REPORT "TYPE:name\n";
	print REPORT "#\n";
	
	my $dbhandle;
	$dbhandle = DBI->connect ("DBI:mysql:host=$DBHOST:port=$DBPORT;database=$DBNAME",$DBUSER,$DBPASS,$DBIARGS);
	if (!($dbhandle)) { &DEAD_JIM; }

	my $queryhandle;
	$queryhandle = $dbhandle->prepare ("SELECT DISTINCT filename FROM $DUPTBL");
	$queryhandle->execute();
	
	my $rows = 0;
	my $namevalue;
	my @namevalues;
	while (my @value = $queryhandle->fetchrow_array() )
	{
		$namevalue = $value[0];
		$namevalue =~ s/\s//g;
		unshift (@namevalues,$namevalue);
		$rows++;
	}
	$queryhandle->finish();
	print "DEBUG: PROCESS_NAME: $rows unique filename blobs found\n" if $DEBUG;

	while ($namevalue = shift(@namevalues))
	{
		my $count;
		$count = $dbhandle->selectrow_array ("SELECT COUNT(*) FROM $DUPTBL WHERE filename=?", undef, $namevalue);
		if ($count > 1)
		{
			print REPORT "ENTRY:$namevalue\n";
			print "ENTRY:$namevalue\n" if $DEBUG;
			
			$queryhandle = $dbhandle->
				prepare ("SELECT fullfilename,size FROM $DUPTBL WHERE filename=?");
			$queryhandle->execute($namevalue);
			while ($rows = $queryhandle->fetchrow_arrayref())
			{
				if (-e $REPORT_FILE)
				{
					print REPORT "VALUE: $rows->[0]\n";
					print REPORT "SIZE: $rows->[1]\n" if $INCLUDE_SIZE;
				}
				else
				{
					print "VALUE: $rows->[0]\n";
					print "SIZE: $rows->[1]\n";
				}
				print "VALUE: $rows->[0]\n" if $DEBUG;
				print "SIZE: $rows->[1]\n" if $DEBUG;
			}
			$queryhandle->finish();
			print REPORT "#\n";
		}
	}	

	$dbhandle->disconnect ();
	
	print "#\n";
	close (REPORT);
}


sub ADDFILES
{
	my ($filearr, $directory, $parent_dir, $filename, $long_filename, $item_count, @dir_contents);

 	$directory = $_[0];
	$filearr = $_[1];

	$parent_dir = getcwd();
	print "Present directory: $directory\n" if $DEBUG;

	# Begin directory sanity checks
	$directory =~ s/\*\.\*//;	# Minor rewrite cases just in case
	$directory =~ s/\*//;		# Wildcards
	$directory =~ s/\\/\//g;	# Convert DOS (back) slashes to forward slashes
	if ($directory eq '')
	{
		$directory = $parent_dir;
		print "No present directory. New add directory: $directory\n" if $DEBUG;	
	}
	if (!(-d $directory))
	{
		if ($parent_dir =~ /$DIRSEP\Z/)
		{
			$directory = "$parent_dir$DIRSEP$directory"; 
			print "Not a full path (trailing $DIRSEP). Add directory now: $directory\n" if $DEBUG;	
		}
		else
		{
			$directory = "$parent_dir$directory"; 
			print "Not a full path (no trailing $DIRSEP). Add directory now: $directory\n" if $DEBUG;	
		}
	}
	# End directory sanity checks
	
	opendir(DIR, $directory) || die("Couldn't open directory $directory for reading.\n");
	@dir_contents = readdir(DIR);
	closedir(DIR);
	
	$item_count = @dir_contents;
	print "Current branch found $item_count entries.\n" if $DEBUG;
	
	while ($filename = pop(@dir_contents))
	{
#print "Filename: $filename\n"; 
		$long_filename = "$directory$DIRSEP$filename";
		$long_filename =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;	# A failsafe
#print "Long filename: $long_filename\n";

		if (-f $long_filename)
		{
			unshift(@files,$long_filename);
			print "Added: $long_filename\n" if $DEBUG;
		}
		else
		{
			if (-d $long_filename)
			{
				# We have to trap a large number of UNIX and Windows directories.
				# Others can easily be added
				if (!(	($filename eq '.') ||
					($filename eq '..') || 
					(-l $long_filename) ||
					# End of UNIX system exceptions
					($filename eq 'proc') || 
					($filename eq '.AppleDesktop') || 
					($filename eq '.AppleDouble') ||  
					($filename eq '.finderinfo') || 
					($filename eq '.resource') ||  
					($filename eq '.xvpics') ||
					# End of UNIX userspace exceptions
					($filename =~ /recycled/i) ||
					($filename =~ /System Volume Information/i)
					# End of Win userspace exceptions
					) )
				{
					# Found a new subdirectory, so we call ADDFILES recursively
					&ADDFILES($long_filename, 0)
				}
			}
		}
		
	}
}
# END Main directory building routines

sub DO_KEY
{
	my ($chopvalue,$holdvalue);
	my $value;

	$value = $_[0];
	
	while ($value =~/$DIRSEP/)	# Strip off directory
	{
		$value =~s/(.*)$DIRSEP(.*)\b/$2/;
		print "DEBUG: DO_KEY: Value in: $value\n" if $DEBUG;
	}

	$value=~s/\.{1,}/\./g;  # Replace .. or ... etc with .
	print "DEBUG: DO_KEY: Value dots: $value\n" if $DEBUG;

	$value=~s/\+//g;	#Kill the plus sign
	print "DEBUG: DO_KEY: Value plus: $value\n" if $DEBUG;

	if ($KEEP_SUFFIX == 0)	# Not using suffix when comparing
	{
		$chopvalue = undef;
		$value =~/(.*)\.(.*)/;
		{
			$chopvalue = "$1";
		}
		if (defined ($chopvalue))
		{
			$value = $chopvalue;
		}
	}
	print "DEBUG: DO_KEY: Value not keep_suffix: $value\n" if $DEBUG;

	if ($DASH_TO_UNDERS != 0)	# Convert dashes to underscores
	{
		$value =~s/-/_/g;
	}
	print "DEBUG: DO_KEY: Value dash to underscore: $value\n" if $DEBUG;

	$value =~tr/[A-Z]/[a-z]/;	# Lowercase all characters
	print "DEBUG: DO_KEY: Value to lowercase: $value\n" if $DEBUG;

	$value =~ s/\(\d*\)//g;
	print "DEBUG: DO_KEY: Value dropping (#*): $value\n" if $DEBUG;

	$value =~ s/copy\s*of\s*//gi;
	print "DEBUG: DO_KEY: Value dropping Copy of: $value\n" if $DEBUG;

	$value =~ s/\s//gi;
	print "DEBUG: DO_KEY: Value dropping whitespace: $value\n" if $DEBUG;

	# Insert other filter arguments here -- be sure to rebuild and reload datasets
	# after changing these, otherwise the name checks will not be consistant
	

	print "DEBUG: DO_KEY: Value final: $value\n" if $DEBUG;

	return ($value);
}

sub DO_CKSUM
{
	my ($SUMFILE, $checksum, $md5);
	$SUMFILE = $_[0];

	print "DEBUG: DO_CKSUM: Opening $SUMFILE for checksum\n" if $DEBUG;
	open(FILEIN, $SUMFILE) || die("Couldn't open $SUMFILE for checksum calculation");

	if ($CKSUM_TYPE =~ /md5/)
	{
		undef $/;
		$md5 = Digest::MD5->new;
		while (<FILEIN>)
		{
			$md5->add($_);
		}
		$checksum = $md5->hexdigest;
	}
	elsif ($CKSUM_TYPE =~ /sysV/)
	{
		# Standard SysV Checksum without the 16b modulo
		undef $/;
		$checksum = unpack("%32C*",<FILEIN>);
	}
	close(FILEIN);
	return ($checksum);
}

sub DO_PARTCKSUM
{
	my ($SUMFILE, $checksum, $md5);
	my $dsize = 512000;	# Number of bytes to read in for the partial checksum
	my $dbuf;

	$SUMFILE = $_[0];
	
	if (&DO_SIZE($SUMFILE) < $dsize)
	{
		print "DEBUG: Passing on partial checksum. $SUMFILE is less than $dsize bytes.\n";
		$checksum = 0;
	}
	else
	{
		print "DEBUG: Opening $SUMFILE for partial checksum\n" if $DEBUG;
		open(FILEIN, $SUMFILE) || die("Couldn't open $SUMFILE for checksum calculation");
		binmode FILEIN;
		
		if (sysread(FILEIN, $dbuf, $dsize))
		{
			my $dlength;
			
#			$dbuf = substr($dbuf,0,$dsize);

			$dlength = length($dbuf);
			print "DEBUG: DO_PARTCKSUM: dbuf length $dlength\n" if $DEBUG;
			
			if ($CKSUM_TYPE =~ /md5/)
			{
				undef $/;
				$md5 = Digest::MD5->new;
				
				$md5->add($dbuf);
			
				$checksum = $md5->hexdigest;
			}
			elsif ($CKSUM_TYPE =~ /sysV/)
			{
				# Standard SysV Checksum without the 16b modulus
				undef $/;
				$checksum = unpack("%32C*",$dbuf);
			}
		}
		else
		{
			print "DEBUG: Error doing block read for partial checksum for $SUMFILE\n";
		}
		close(FILEIN);
	}
	return ($checksum);
}

sub DO_SIZE
{
	my ($value,$size, $void);
	
	$value = $_[0];
	

	($void,$void,$void,$void,$void,$void,$void,$size,$void,$void,$void,$void,$void) =
						stat($value);
	print "DEBUG: DO_SIZE: $size $value\n" if $DEBUG;
	return ($size);
}

sub DEAD_JIM
{
	print "Unable to connect to the database with the following settings:\n";
	print "DBHOST = $DBHOST\nDBPORT = $DBPORT\nDBUSER = $DBUSER\n";
	print "DBPASS = <hidden>\nDBNAME = $DBNAME\nDUPTBL = $DUPTBL\n";
	print "DBIARGS = $DBIARGS\n";
	die ("Check the above settings, make sure the correct DB is online with the correct access permissions.\n");
}

sub GET_TIME
{
	my ($sec,$min,$hour,$mday,$mon,$year,$void,$datestr);
	
	($sec,$min,$hour,$mday,$mon,$year,$void) = localtime(time());
	
	$year = $year + 1900;
	$mon++;
	if ($mon < 9)
	{
		$mon = "0$mon";
	}
	if ($mday < 9)
	{
		$mday = "0$mday";
	}
	
	print "DEBUG: GET_TIME: Time is: $year$mon$mday $hour:$min\n" if $DEBUG;
	return "$year$mon$mday $hour:$min";
}