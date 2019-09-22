#!/usr/bin/perl -w

use strict;
use utf8;
use Data::Dumper;
use Getopt::Long;


my $csvname = "advdm.csv";
my $baseURI;
my $user;
my $pass;

GetOptions ("url=s" => \$baseURI, "file=s" => \$csvname, "user=s"  => \$user, "pass=s"  => \$pass) or die("Error in command line arguments\n");

if (!(defined($baseURI)))
{
    die("url needs to be set\n");
}

if (!(defined($user)))
{
    die("user needs to be set\n");
}

if (!(defined($pass)))
{
    die("pass needs to be set\n");
}

{
    package MacParser;
    use base qw(HTML::Parser);
    use LWP::UserAgent;
    use LWP::Protocol::https;
    use HTTP::Cookies::Netscape;
    use URI::Escape;
    use HTML::Entities;
    use Encode;
    use File::Spec;

    my $self;

    sub LWP::UserAgent::redirect_ok 
    {
       my ($self, $request) = @_;
       $request->method("GET"),$request->content("") if $request->method eq "POST";
       1;

    }

    our $ua = LWP::UserAgent->new;

    $self->{cookieJar} = 'advdmwish';
    $ua->cookie_jar(HTTP::Cookies::Netscape->new('file' => "$self->{cookieJar}",'autosave' => 1,));

    sub new
    {
        my $proto = shift;
        my $class = ref($proto) || $proto;
        my $self  = $class->SUPER::new();

        $ua->agent('Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.5) Gecko/20041111 Firefox/1.0');
        $ua->ssl_opts(verify_hostname => 0);
        $ua->default_header('Accept-Encoding' => 'x-gzip');
        $ua->default_header('Accept' => 'text/html, application/xml');
        $self->{ua} = $ua;

        $self->{itemIdx} = -1;
        $self->{itemsList} = ();

# Parsing variables
        $self->{dataTitle} = undef;
        $self->{dataStudio} = undef;
        $self->{dataPrice} = undef;
        $self->{dataComment} = undef;
        $self->{inTR} = 0;
        $self->{inHREF} = 0;
        $self->{inTitle} = 0;
        $self->{inTitleBlock} = 0;
#print "UNSET inTitleBlock\n";
        $self->{inPrice} = 0;
        $self->{inComment} = 0;
        $self->{inComment2} = 0;
        $self->{dataArray} = [];

        bless ($self, $class);
        return $self;
    }

    sub getItemsNumber
    {
        my ($self) = @_;

        return $self->{itemIdx} + 1;
    }

    sub getItems
    {
        my ($self) = @_;
        return @{$self->{itemsList}};
    }

    sub load
    {
        my ($self, $url, $post, $noSave) = @_;
         
        $self->{itemIdx} = -1;
        $self->{isInfo} = 0;
        $self->{itemsList} = ();

        my $html;
        
        $html = $self->loadPage($url,$post);

        return if (length $html eq 0);
        $self->{parsingList} = 1;
        decode_entities($html)
            if $self->decodeEntitiesWanted;
        $self->{inside} = undef;
        $self->parse($html);

        return $self->{dataArray};
#print $html;        
    }
    
    sub loadPage
    {
        my ($self, $url, $post, $noSave) = @_;
#print "$url\n";
#print "$post\n";
        $self->{loadedUrl} = $url if ! $noSave;
        my $response;
        my $result;
            if ($post)
            {
#                $ua->ssl_opts( SSL_hostname => 'www.adultdvdmarketplace.com' );
                $response = $ua->post($url, $post);
            }
            else
            {
                $response = $ua->get($url);
            }

my $d = Data::Dumper->new([$response]);
print $d->Dump;
            #UnclePetros 03/07/2011:
            #code to handle correctly 301 and 302 response messages
            if($response->code == '301' || $response->code == '302'){
                my $location = $response->header("location");
                $response = $ua->get($location);
                $self->{loadedUrl} = $location;
#my $d = Data::Dumper->new([$response]);
#print $d->Dump;
            }

            if ($response->code ne '200')
            {
                print "PluginsBase response ".$response->code." url ".$url."\n";
                return "";
            }
            eval {
                $result = $response->decoded_content;
#print $result;
            };
        return $result || ($response && $response->content);
    }
    
    sub capWord
    {
        my ($self, $msg) = @_;
        
        use locale;
        
        (my $newmsg = lc $msg) =~ s/(\s|,|^)(\w)(\w)(\w*?)/$1\U$2\E$3$4/gi;
        return $newmsg;
    }

    sub getSearchFieldsArray
    {
        return [''];
    }

    sub getSearchFields
    {
        my ($self, $model) = @_;
        
        my $result = '';
        $result .= $model->getDisplayedLabel($_).', ' foreach (@{$self->getSearchFieldsArray});
        $result =~ s/, $//;
        return $result;
    }

    sub hasField
    {
        my ($self, $field) = @_;
    
        return $self->{hasField}->{$field};
    }

    sub getExtra
    {
        return '';
    }

    # Character set for web page text
    sub getCharset
    {
        my $self = shift;
    
        return "ISO-8859-1";
    }
    
    # Character set for encoding search term, can sometimes be different
    # to the page encoding, but we default to the same as the page set
    sub getSearchCharset
    {
        my $self = shift;
    
        return getCharset;
    }
    
    # For some plugins, we need extra checks to determine if urls match
    # the language the plugin is written for. This allows us to correctly determine
    # if a drag and dropped url is handled by a particular plugin. If these
    # checks are necessary, return 1, and make sure plugin handles the 
    # the testURL function correctly
    sub needsLanguageTest
    {
        return 0;
    }   
    
    # Used to test if a given url is handled by the plugin. Only required if 
    # needsLanguageTest is true.
    sub testURL
    {
        my ($self, $url) = @_;    
        return 1
    }
    
    # Determines whether plugin should be the default plugins gcstar uses.
    # Plugins with this attribute set will appear first in plugin list,
    # and will be highlighted with a star icon. A returned value of 1 
    # means the plugin is preferred if it's language matches the user's language,
    # a returned value of 2 mean's it's preferred regardless of the language.
    sub isPreferred
    {
        return 0;
    }
    
    sub getPreferred
    {
        return isPreferred;
    }
    
    sub getNotConverted
    {
        my $self = shift;
        return [];
    }

    sub decodeEntitiesWanted
    {
        return 1;
    }

    sub getDefaultPictureSuffix
    {
        return '';
    }

    sub convertCharset
    {
        my ($self, $value) = @_;

        my $result = $value;
        if (ref($value) eq 'ARRAY')
        {
            foreach my $line(@{$value})
            {
                my $i = 0;
                # some sites don't follow their own encoding
                eval {
                    map {$_ = decode($self->getCharset, $_)} @{$line};
                };
                warn "In PluginsBase ".$@ if $@;
            }
        }
        else
        {
            eval {
                $result = decode($self->getCharset, $result);
            };
        }
        return $result;
    }
    
    sub getItemInfo
    {
        my $self = shift;

        eval {
            $self->init;
        };
        my $idx = $self->{wantedIdx};
        my $url = $self->getItemUrl($self->{itemsList}[$idx]->{url});
        $self->{curInfo} = {};
        $self->loadUrl($url);

        # multi-pass plugins that requires multiple web page to get all info on a single collection item
        # for example : Allmovie (tabs to get casting), Allocine (idem)
        # the plugin can set {nextUrl} to fetch next web page, the information is cumulative in {curInfo}
        while ($self->{curInfo}->{nextUrl})
        {
            my $nextUrl = $self->{curInfo}->{nextUrl};
            $self->{curInfo}->{nextUrl} = 0;
            $self->loadUrl($nextUrl);
        }
        return $self->{curInfo};
    }
        
    sub changeUrl
    {
        my ($self, $url) = @_;

        return $url;
    }
    
    sub setProxy
    {
        my ($self, $proxy) = @_;
        $self->{proxy} = $proxy;
    }
    
    sub checkProxy
    {
        my $self = shift;
        $ua->proxy(['http','https'], $self->{proxy});
    }
    
    sub start
    {
        my ($self, $tagname, $attr, $attrseq, $origtext) = @_;
        $self->{inside}->{$tagname}++;

#print "Tag: $tagname\n";
#if ($attr->{'colspan'}) { print "Attr: $attr->{'colspan'}\n"; }

        if ($tagname eq 'hr')
        {
# Reset for next title
# Write out the entry if it is complete
             if ($self->{dataTitle})
             {
                if (!defined($self->{dataComment}))
                {
                    $self->{dataComment} =  ' ';
                }
                push $self->{dataArray}, "$self->{dataTitle},$self->{dataStudio},$self->{dataPrice},$self->{dataComment}\n";
             }
# Clear the flags
             $self->{dataTitle} = undef;
             $self->{dataStudio} = undef;
             $self->{dataPrice} = undef;
             $self->{dataComment} = undef;
             $self->{inTR} = 0;
             $self->{inTitleBlock} = 0;
#print "UNSET inTitleBlock\n";
             $self->{inTitle} = 0;
        }
        elsif (($tagname eq 'input') && ($attr->{type} eq 'checkbox'))
        {
            $self->{inTitleBlock} = 1;
#print "SET inTitleBlock\n";        
        }
        elsif ($self->{inTitleBlock} && ($tagname eq 'a') && $attr->{'href'})
        {
            if ($attr->{'href'} =~ /dvd_view/)
            {
                $self->{inTitle} = 1;
            }
        }
        elsif ($self->{inTitleBlock} && ($tagname eq 'td') && $attr->{'nowrap'})
        {
            if ($attr->{'nowrap'} eq 'nowrap')
            {
                $self->{inPrice} = 1;
            }
        }
        elsif ($self->{inTitleBlock} && ($tagname eq 'td') && $attr->{'colspan'})
        {
#print "IN td Block\n";
            if ($attr->{'colspan'} eq '4')
            {
                $self->{inComment} = 1;
#print "SET inComment\n";
            }
        }
        elsif ($self->{inComment} && ($tagname eq 'font'))
        {
            $self->{inComment2} = 1;   
#print "SET inComment2\n";
        }
    }

    sub end
    {
        my ($self, $tagname) = @_;
        $self->{inside}->{$tagname}--;
        if ($tagname eq 'tr')
        {
             $self->{inTR} = 0;

        }
        elsif ($tagname eq 'a')
        {
             $self->{inHREF} = 0;
        }
        elsif ($tagname eq 'td')
        {
             $self->{inStudio} = 0; 
             $self->{inPrice} = 0;    
             $self->{inComment} = 0;
        }
        elsif ($tagname eq 'font')
        {
             $self->{inComment2} = 0;
        }
    }

    sub text
    {
        my ($self, $origtext) = @_;
        return if length($origtext) < 2;
#        return if ($self->{parsingEnded});
        $origtext =~ s/^\s*//;
        $origtext =~ s/\s$//;
        $origtext =~ s/\s{2,}/ /g;
        $origtext =~ s/^,$//;
			
        if ($self->{inStudio})
        {
				$self->{dataStudio} = $origtext;
            $self->{inStudio} = 0;
        }
        elsif ($self->{inTitle})
        { 
           	if ($origtext ne '')
           	{
                  $origtext =~ s/\,/\_/g;
               	$self->{dataTitle} = $origtext;
           			$self->{inTitle} = 0;
                  $self->{inStudio} = 1;
            }
        }
        elsif ($self->{inPrice})
        {
            $self->{dataPrice} = $origtext;
        }
        elsif ($self->{inComment} && $self->{inComment2})
        {
#print "In inComment\n";
            $origtext =~ s/\&nbsp\;/\?/g;

            $origtext =~ s/\?-\?//;
            $origtext =~ s/-\s//;
            $self->{dataComment} = $origtext;
        }            
        elsif ($origtext =~ /Page\s(\d+)\sof\s(\d+)/)
        {
            $self->{iterTotal} = $2;
#print "iterTotal set to $self->{iterTotal}\n";
        }
    } 

}

my $connection;
my $main = MacParser->new(); 

# Open and print the CSV header line
my $csvf; 
open($csvf, '>', $csvname) || die("Error: Cannot open CSV file $csvf for writing.\n"); 
print $csvf "Title,Studio,Price,Comment\n";

$main->{cookieJar}="getadvdmwish";
$main->{iterTotal}=undef;
$main->{iterCurrent}=1;

# Authentication
$main->load("$baseURI/xcart/adult_dvd/login.php", ['mode' => 'login', 'adult_dvd_id' => '', 'usertype' => 'C', 'username' => $user, 'password' => $pass, 'redirect' => 'adult_dvd']);

# Inital Load
$main->load("$baseURI/xcart/adult_dvd/alerts.php?order_by=title&seller_login=&page=1");

#my $d = Data::Dumper->new($main->{dataArray});
#print $d->Dump;

my $item;
while (defined($item = shift $main->{dataArray}))
{
     print $csvf $item;
}

# Rest of the pages
$main->{iterCurrent}++;
while ($main->{iterCurrent} <= $main->{iterTotal}) 
{
print "In page $main->{iterCurrent}...\n";
    $main->load("$baseURI/xcart/adult_dvd/alerts.php?order_by=title&seller_login=&page=$main->{iterCurrent}");
    while (defined($item = shift $main->{dataArray}))
    {
        print $csvf $item;
    }
    $main->{iterCurrent}++;
    sleep(1);
}
close $csvf;

1;
