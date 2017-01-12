find . -maxdepth 1 -size +2M -type f -exec file {} ';' |grep ': data' | cut --delimiter=':' -f 1 | xargs -I {} mv {} _bad/

