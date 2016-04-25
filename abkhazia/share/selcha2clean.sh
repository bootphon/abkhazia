#!/usr/bin/env bash
# Copyright 2015, 2016 Alex Cristia alecristia@gmail.com
# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.


# cleaning up selected lines from cha files before generating a phono
# format


#Variables that have been passed by the user
selfile=$1
ortho=$2

# tmp=$(mktemp tmp.XXXX)
# trap EXIT "rm -f $tmp"

echo "Cleaning $selfile"

# Replacements to clean up punctuation, etc. -- usually ok regardless
# of the corpus. We keep the timestamp in this version of the script
iconv -f ISO-8859-1 $selfile |
    sed 's/@Media.*//g' |
    sed 's/^....:.//g' |
    # sed "s/\_/ /g" |
    # sed '/^0(.*) .$/d' |
    # sed  's/.*$//g' |
    sed 's///g' |
    tr -d '\"' |
    tr -d '\"' |
    tr -d '\/' |
    sed 's/\+/ /g' |
    tr -d '\.' |
    tr -d '\?' |
    tr -d '!' |
    tr -d ';' |
    tr -d '\<' |
    tr -d '\>' |
    tr -d ','  |
    tr -d ':'  |
    sed 's/&[^ ]*//g' |
    grep -v '\[- spa\]' |
    sed 's/[^ ]*@sspa//g' |
    sed 's/\[[^[]*\]//g' |
    sed 's/([^(]*)//g' |
    sed 's/xxx//g' |
    sed 's/www//g' |
    sed 's/XXX//g' |
    sed 's/yyy//g' |
    # sed 's/0*//g' |
    sed 's/@o//g' |
    sed 's/@f//g' |
    sed 's/@q//g' |
    sed 's/@u//g' |
    sed 's/@c//g' |
    sed "s/\' / /g"  |
    sed 's/  / /g' |
    sed 's/ $//g' |
    sed 's/^ //g' |
    sed 's/^[ ]*//g' |
    sed 's/ $//g' |
    sed '/^$/d' |
    sed '/^ $/d' |
    awk '{gsub("\"",""); print}' |  # > $tmp
    #********** A T T E N T I O N ***************
    # check that the next set of replacements for unusual spellings is
    # adapted to our purposes
    sed 's/allgone/all gone/g' |  # $tmp |
    #sed 's/[0-9]//g' |
    sed 's/whaddaya/what do you/g' |
    sed 's/whadda/what do/g' |
    sed 's/haveto/have to/g' |
    sed 's/hasto/has to/g' |
    sed 's/outof/out of/g' |
    sed 's/lotsof/lots of/g' |
    sed 's/lotta/lots of/g' |
    sed 's/alotof/a lot of/g' |
    sed "s/wha\'s/what's/g" |
    sed "s/this\'s/this is/g" |
    sed 's/chya/ you/g' |
    sed 's/tcha/t you/g' |
    sed 's/dya /d you /g' |
    sed 's/chyou/ you/g' |
    sed "s/dont you/don\'t you/g" |
    sed 's/wanta/wanna/g'  |
    sed "s/whats / what\'s /g" |
    sed "s/'re/ are/g" |
    sed "s/klenex/kleenex/g" |
    sed 's/yogourt/yogurt/g' |
    sed 's/weee*/wee/g' |
    sed 's/oooo*/oh/g' |
    sed 's/ oo / oh /g' |
    sed 's/ohh/oh/g' |
    sed "s/ im / I\'m /g" |
    tr -d '\t' |
    sed '/^$/d' |
    iconv -t ISO-8859-1 > $ortho

# This is to process all the "junk" that were generated when making
# the changes from included to ortho.  For e.g., the cleaning process
# generated double spaces between 2 words (while not present in
# included)
sed -i -e 's/  $//g' $ortho
sed -i -e 's/  / /g' $ortho
# sed -i -e 's/  / /g' $ortho  # not same encoding as above?
sed -i -e 's/^ //g' $ortho
sed -i -e 's/ $//g' $ortho
sed -i -e 's/”//g' $ortho
sed -i -e 's/“//g' $ortho
