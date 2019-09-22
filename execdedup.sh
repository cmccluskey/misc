#!/bin/bash

# Created with find . -name \*.Id_\*
# Then filtered with sed 's%/[^/]*$%/%' | uniq

IFS=$'\n'
BASE=$(pwd)

for file in $(<IDs.txt)
do
#  file=$(printf '%q' "$file")
  cd "$BASE/$file"
  /Users/chrismccluskey/git/misc/dedupLocalFileorig.py -d '*'   
done
