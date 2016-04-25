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


# Selecting speakers from cha files in prep to generating a phono
# format. IMPORTANT!! Includes data selection

#########VARIABLES
#Variables that have been passed by the user
chafile=$1
selfile=$2
#########

[ ! -f $chafile ] && { echo "$chafile not found"; exit 1; }
echo "selecting speakers from $chafile"


#********** A T T E N T I O N ***************

# Modify this section to select the lines you want, for example here,
# we exclude speech by children and non-humans.
# List of specific names we needed to add to eliminate speech from target child and non-adults:
#
# Bloom70/Peter/*.cha	JEN	Child
# Bloom70/Peter/*.cha	JEN	Sister
# Brent/w1-1005.cha	MAG	Target_Child
# Brown/Adam/*.cha	CEC	Cousin
# Brown/Adam/adam23.cha	PAU	Brother
# Brown/Sarah/sarah019.cha	ANN	Cousin
# Brown/Sarah/sarah020.cha	JOA	Child
# Brown/Sarah/sarah046.cha	SAN	Playmate
# Clark/shem15.cha	BRU	Child
# Clark/shem15.cha	CAR	Child
# Clark/shem15.cha	LEN	Child
# Clark/shem37.cha	JEM	Child
# Cornell/moore189.cha	JOS	Child
# Feldman/09.cha	STV	Target_Child
# Feldman/*.cha	LAR	Child
# MacWhinney/08a.cha	MAD	Child
# MacWhinney/*.cha	MAR	Brother
# Sachs/n61na.cha	JEN	Playmate
# Weist/Roman/rom*.cha	SOP	Sister

iconv -f ISO-8859-1 "$chafile" |
    grep -i '^*\|@Media' |
    # leave this line uncommented to get rid of all child speakers
    grep -v 'SI.\|BR.\|CHI\|TO.\|ENV\|BOY\|NON\|MAG\|JEN\|MAG\|CEC\|PAU\|ANN\|JOA\|SAN\|BRU\|CAR\|LEN\|JEM\|JOS\|STV\|LAR\|MAD\|MAR\|SOP' |
    # leave this line uncommented to focus only on mother's speech
    #grep 'MOT' |
    iconv -t ISO-8859-1 > $selfile
