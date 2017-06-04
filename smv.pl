#! C:/Perl/bin/perl.exe -w
########################################################################
# NOTES:
#
# 20020718	Inital tests completed, and checked out on several real tests
# under Windows. Ready for use on Windows platform.
#
#
# TODO:
#
# 20020718	Need to do checking on UNIX side to verify that the windows 
# specific patches caused no harm.
# 20020804	Full paths on source cause recursive directory creation. May need reproduce tree switch.
#
use strict;
use Cwd;

my $DEBUG = 0;
my $VERSION ="2.1";

my $OS_TYPE = "WINDOWS";
my $NOTUNIX = 0;

my $DIRSEP = '/';

my ($MOVECMD, $MOVECMD_FORCE);
if ($OS_TYPE =~ /UNIX/)
{
	$MOVECMD = "mv";
	$MOVECMD_FORCE = "-f";
}
elsif ($OS_TYPE =~ /WINDOWS/)
{
	$MOVECMD = "move";
	$MOVECMD_FORCE = "/Y";
	$NOTUNIX = 1;
}

my $USE_MD5 = 1;
my $OVER_FLAG = 0;
my $FORCE_FLAG = 0;
my $VERBOSE_FLAG = 0;
my $RECURSE_FLAG = 0;

# Try everything but the move.
my $FILE_SAFE = 0;

print "$OS_TYPE Version\n" if ($VERBOSE_FLAG || $DEBUG);

if ($USE_MD5)
{
	use Digest::MD5;
}
########################################################################

########################################################################
# START Subroutines

sub USAGE
{
	print "usage: smv -f -o -v <SOURCE> <DEST>\n";
	print "\t-f  Forces SOURCE files to overwrite DEST files disreguarding content\n";
	print "\t-o  If the file is the same, remove the DEST version of the file\n";
	print "\t-r  Recurse into matching directories\n";
	print "\t-v  Turns verbose reporting on\n";
	exit;
}

sub CKSUM
{
	my ($checksum, $md5);
	my $SUMFILE = $_[0];
	print "Opening $SUMFILE for checksum\n" if $DEBUG;
	open(FILEIN, $SUMFILE) || die("Couldn't open $SUMFILE for checksum calculation");

	if ($USE_MD5)
	{
		$md5 = Digest::MD5->new;
		while (<FILEIN>)
		{
			$md5->add($_);
		}
		$checksum = $md5->hexdigest;
	}
	else
	{
		# Standard SysV Checksum
		undef $/;
		$checksum = unpack("%32C*",<FILEIN>);
	}
	close(FILEIN);
	return ($checksum);
}

sub ADDFILES
{
	my ($filearr, $directory, $parent_dir, $filename, $long_filename, $item_count, @dir_contents);
	my ($pre_wild, $post_wild);

 	$directory = $_[0];
	$filearr = $_[1];
	$pre_wild = $_[2];
	$post_wild = $_[3];
	
	$parent_dir = getcwd();
	if (!defined($directory))
	{
		$directory = $parent_dir;
		print "No present directory. New add directory: $directory\n" if ($DEBUG);	
	}
	print "Present directory: $directory\n" if ($DEBUG);

	# Begin directory sanity checks
 
	$directory =~ s/\*\.\*//;	# Minor rewrite cases just in case
	$directory =~ s/\*//;		# Wildcards
	$directory =~ s/\\/$DIRSEP/g;	# Convert DOS (back) slashes to forward slashes
#	if (!(-d $directory))
#	{
#		if ($parent_dir =~ /$DIRSEP\Z/)
#		{
#			$directory = "$parent_dir$DIRSEP$directory"; 
#			print "Not a full path (trailing $DIRSEP). Add directory now: $directory\n" if ($DEBUG);	
#		}
#		else
#		{
#			$directory = "$parent_dir$directory"; 
#			print "Not a full path (no trailing $DIRSEP). Add directory now: $directory\n" if ($DEBUG);	
#		}
#	}
	# End directory sanity checks
		
	opendir(DIR, $directory) || die("Couldn't open directory $directory for reading.\n");
	@dir_contents = readdir(DIR);
	closedir(DIR);
	
	$item_count = @dir_contents;
	print "Current branch found $item_count entries.\n" if ($DEBUG);
	
	while ($filename = pop(@dir_contents))
	{
		print "Current filename: $filename\n" if $DEBUG;
		$long_filename = "$directory$DIRSEP$filename";
		$long_filename =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;	# A failsafe

		if (-f $long_filename)
		{
			if ($NOTUNIX)
			{
				if (defined($pre_wild)||defined($post_wild))
				{
					if (($filename =~ /^$pre_wild/i) && ($filename =~ /$post_wild$/i) )
					{	
						print "Wildacard match found:\n" if $DEBUG;
						unshift(@$filearr,$long_filename);
						print "Added: $long_filename\n" if ($DEBUG);
					}
				}
				else
				{
					unshift(@$filearr,$long_filename);
					print "Added: $long_filename\n" if ($DEBUG);
				}
			}
			else
			{
				unshift(@$filearr,$long_filename);
				print "Added: $long_filename\n" if ($DEBUG);
			}
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
					($filename =~ /recycled/i) 
					# End of Win userspace exceptions
					) )
				{
					# Found a new subdirectory, so we call ADDFILES recursively
					if ($RECURSE_FLAG)
					{
						if ($NOTUNIX)
						{
							if ($filename =~ /$pre_wild(.*?)$post_wild/i)
							{	
								print "Wildcard directory match found\n" if $DEBUG;
								&ADDFILES($long_filename, $filearr, $pre_wild, $post_wild);
	
							}
							else
							{
								&ADDFILES($long_filename, $filearr, $pre_wild, $post_wild);
							}
						}
						else
						{
								&ADDFILES($long_filename, $filearr, $pre_wild, $post_wild);
						}
					}
				}
			}
		}
		
	}
}

sub CREATE_PATH
{
	my $filename = $_[0];
	my $dirname;
	my (@junk, $count, $wd, $i);
	
	@junk = split(/$DIRSEP/, $filename);
	$count = @junk;

	$wd = getcwd();
	$wd =~ s/\\/\//g;
	$wd =~ s/\/\//\//g;
	$filename =~ s/$wd//;

	if ($OS_TYPE =~ /^WINDOWS/) { $count = $count - 1; };
	if ($OS_TYPE =~ /^UNIX/) { $count = $count - 0; };

#	print "Count: $count\n";
	for ($i=$count ; $i > 0; $i--)
	{
		$dirname = $filename;
	

		$dirname =~ s/(.*)($DIRSEP[^$DIRSEP]*){$i,$i}/$1/;
		print "$i: $dirname\n" if $DEBUG;
		if (mkdir($dirname))
		{
			print "MKDIR $dirname suceeded\n" if $DEBUG;
		}
		else
		{
			if (-d $dirname)
			{
				# Well, it's there!
			}
			else
			{
				die ("MKDIR failed for directory $dirname");
			}
		}
	}
}


########################################################################
# MAIN Code

my $ARGCOUNT = @ARGV;
print "$ARGCOUNT\n" if $DEBUG;


my $MULTITEST = @ARGV;
print $MULTITEST if $DEBUG;

if ($MULTITEST < 2)
{
	&USAGE;
}

my ($DEST_ISDIR);
my $DESTINATION = pop(@ARGV);
print "Dest: $DESTINATION\n" if $DEBUG;
if (-d $DESTINATION)
{
	$DEST_ISDIR = 1;
}
else
{
	$DEST_ISDIR = 0;
}


my @FILES;	# Main list of files
my $FLAGTEST;
my ($scrap1, $scrap2);
my $currentdir;

while ($FLAGTEST = shift(@ARGV))
{
	if ($FLAGTEST =~ /\A-/)
	{		
		if ($FLAGTEST =~ /-d\b/)
		{
			$DEBUG = 1;
			print "DEBUG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-v\b/)
		{
			$VERBOSE_FLAG = 1;
			print "VERBOSE_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-r\b/)
		{
			$RECURSE_FLAG = 1;
			print "RECURSE_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-o\b/)
		{
			$OVER_FLAG = 1;
			print "OVER_FLAG set\n" if $DEBUG;
		}
		elsif ($FLAGTEST =~ /-f\b/)
		{
			$FORCE_FLAG = 1;
			print "FORCE_FLAG set\n" if $DEBUG;
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
		print "Flagtest: $FLAGTEST\n" if $DEBUG;
		if ($FLAGTEST =~ /\*/)
		{					# Take of OSes that don't parse wildcards on the cmd ln
			if ($NOTUNIX)
			{	
				($scrap1,$scrap2) = split (/\*/,$FLAGTEST);
				print "Wildcard: Before: $scrap1 After: $scrap2\n" if $DEBUG;
				if (defined($scrap1) || defined($scrap2))
				{
					undef($FLAGTEST);
				}
				ADDFILES($FLAGTEST,\@FILES,$scrap1,$scrap2);

			}
			else
			{
				die("This is a non UNIX system. A \* was passed as an agument, but wasn't automatically expanded. Please set NONUNIX in the script.\n");
			}
		}
		else
		{	# Doesn't accept wildcarded intrepreted directories in NOTUNIX
			if (-d $FLAGTEST)
			{
				ADDFILES($FLAGTEST,\@FILES);
			}
			else
			{	
				$currentdir = getcwd();
				$FLAGTEST = "$currentdir$DIRSEP$FLAGTEST";
				$FLAGTEST =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;	# A failsafe
				unshift(@FILES,$FLAGTEST);
			}
		}
	}
}

$MULTITEST = @FILES;
print "MULTITEST: $MULTITEST\n";
if (($MULTITEST > 2) && !(-d $DESTINATION))
{
	print "When moving multiple files the last arument must be a directory.\n\n";
	&USAGE;
}
if ($MULTITEST < 1 )
{
	print "Both a source and destination are required.\n\n";
	&USAGE;
}

my ($CURRFILE, $DESTFILE, $tCURRFILE, $tDESTFILE);
my $current_cwd = getcwd();
while (@FILES)
{
	print "\n" if ($VERBOSE_FLAG || $DEBUG);	

	$CURRFILE = shift(@FILES);

	$CURRFILE =~ s/\\/$DIRSEP/g;
	$CURRFILE =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	$CURRFILE =~ s/$current_cwd//;
	
	$CURRFILE =~ s/\A$DIRSEP//;

	print "CURRFILE: $CURRFILE\n" if ($DEBUG);

	if ($DEST_ISDIR)
	{
		$DESTFILE = "$DESTINATION$DIRSEP$CURRFILE";
		$DESTFILE =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	} 
	else
	{
		$DESTFILE = $DESTINATION;
	}

	$CURRFILE =~ s/\\/$DIRSEP/g;
	$CURRFILE =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	$DESTFILE =~ s/\\/$DIRSEP/g;
	$DESTFILE =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	print "CFile: $CURRFILE\nDFile: $DESTFILE\n" if $DEBUG;
	
	# Setup test cases to see if the file is the same
	$tCURRFILE = $CURRFILE;
	$tDESTFILE = $DESTFILE;
	$tCURRFILE = "$current_cwd$DIRSEP$tCURRFILE";
	$tDESTFILE = "$current_cwd$DIRSEP$tDESTFILE";
	$tCURRFILE =~ s/\\/$DIRSEP/g;
	$tCURRFILE =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	$tDESTFILE =~ s/\\/$DIRSEP/g;
	$tDESTFILE =~ s/$DIRSEP$DIRSEP/$DIRSEP/g;
	$tCURRFILE =~ s/$DIRSEP[^$DIRSEP]*$DIRSEP\.\.$DIRSEP/$DIRSEP/g;
	$tCURRFILE =~ s/$DIRSEP[^$DIRSEP]*\.\.$DIRSEP/$DIRSEP/g;
	$tDESTFILE =~ s/$DIRSEP[^$DIRSEP]*$DIRSEP\.\.$DIRSEP/$DIRSEP/g;
	$tDESTFILE =~ s/$DIRSEP[^$DIRSEP]*\.\.$DIRSEP/$DIRSEP/g;
	$tCURRFILE =~ s/\/\.\//\//g;
	$tDESTFILE =~ s/\/\.\//\//g;

	
	print "tCFile: $tCURRFILE\ntDFile: $tDESTFILE\n" if $DEBUG;
	
	if ($tDESTFILE eq $tCURRFILE)
	{
		print "The file $CURRFILE is the same.\n" if ($VERBOSE_FLAG || $DEBUG);
	}
	else
	{
		CREATE_PATH($DESTFILE);	
	
		if (-f $DESTFILE)
		{
			my $CURRFILE_SUM = CKSUM($CURRFILE);
			my $DESTFILE_SUM = CKSUM($DESTFILE);
			print "CFileSUM: $CURRFILE_SUM, DFileSUM: $DESTFILE_SUM\n" if ($DEBUG);
			if ($FORCE_FLAG)
			{
				print "$CURRFILE ->> $DESTFILE\n" if ($VERBOSE_FLAG || $DEBUG);
				if ($FILE_SAFE)
				{
					print "SYSCMD: $MOVECMD $MOVECMD_FORCE \"$CURRFILE\" \"$DESTFILE\"\n";
				}
				else
				{
# Need to do checking for UNIX here
					system("$MOVECMD $MOVECMD_FORCE \"$CURRFILE\" \"$DESTFILE\"");
				}
			}
			elsif ($OVER_FLAG)
			{
				if ($CURRFILE_SUM eq $DESTFILE_SUM)
				{
					print "$CURRFILE --X $DESTFILE\n" if ($VERBOSE_FLAG || $DEBUG);
					if ($FILE_SAFE)
					{
						print "SYSCMD: unlink \"$DESTFILE\"\n";
					}
					else
					{
						unlink($DESTFILE) || die ("Could not perform unlink to file $DESTFILE");
					}
				}
				else
				{
					print "$CURRFILE --- $DESTFILE\n" if ($VERBOSE_FLAG || $DEBUG);
				}
			}
			else
			{
				if ($CURRFILE_SUM eq $DESTFILE_SUM)
				{
					print "$CURRFILE X-- $DESTFILE\n" if ($VERBOSE_FLAG || $DEBUG);
					if ($FILE_SAFE)
					{
						print "SYSCMD: unlink \"$CURRFILE\"\n";
					}
					else
					{
						unlink($CURRFILE) || die ("Could not perform unlink to file $CURRFILE");
					}
				}
				else
				{
					print "$CURRFILE --- $DESTFILE\n" if ($VERBOSE_FLAG || $DEBUG);
				}
			}				
		}
		else
		{
			print "$CURRFILE --> $DESTFILE\n" if ($VERBOSE_FLAG || $DEBUG);
			if ($FILE_SAFE)
			{
				print "SYSCMD: $MOVECMD \"$CURRFILE\" \"$DESTFILE\"\n" if ($VERBOSE_FLAG || $DEBUG);
			}
			else
			{
# Need to do checking for UNIX here
				system("$MOVECMD \"$CURRFILE\" \"$DESTFILE\"");
			}
		}
	} 
}