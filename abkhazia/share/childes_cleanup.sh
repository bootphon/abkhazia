#!/usr/bin/env bash
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


# Wrapper written by Xuan Nga Cao to clean up a large number of
# talkbank+childes corpora, one transcript at a time
#
# The script takes one parent directory with any level of embedding,
# for instance one root folder and sub-folders containing the
# different corpora, each of which contains one transcript per child
# or recording session. For the root folder, it will generate a folder
# bearing the root folder name and containing all the output files
# relative to that root and all the corpora included in it. It
# generates 2 files: one with basic info about the corpus: corpus
# path, filename, child's age, number of speakers, identity of
# speakers, number of adults. The second file will list the processed
# files.


###
# Adapt the following variables, being careful to provide absolute paths
###

# where you have put the talkbank corpora to be analyzed
input_corpus=$(readlink -f $1)

# this is where we will put the processed versions of the transcripts
res_folder=$(readlink -f $2)

# where to find cha2sel.sh and selcha2clean.sh
scriptdir=$(readlink -f $3)


###
# This part of the script does not need to be modified
###

for script in cha2sel.sh selcha2clean.sh; do
    [ -f $scriptdir/$script ] || { echo 'not found $scriptdir/$script.sh'; exit 1; }
done

append1="cha_files"
append2="cds_files"

# create folder that will contain all output files
mkdir -p $res_folder

# loop through all the sub-folders (1 level down)
for corpusfolder in $input_corpus/*/; do
    # cd $corpusfolder

    # get name of corpus and create the folder with that
    # name+APPEND1 - E.g. "Bernstein_cha" (will contain all cha
    # files for Bernstein corpus)
    subcorpus_in=$res_folder/$append1

    mkdir -p $subcorpus_in

    # search and copy all cha files to the relevant corpus
    find $corpusfolder -iname '*.cha' -type f -exec cp {} $subcorpus_in \; || exit 1

    # get name of corpus and create folder with that name+APPEND2 -
    # E.g. "Bernstein_cds" (will contain all output files for
    # Bernstein corpus)
    subcorpus_out=$res_folder/$append2
    #echo $subcorpus_out
    mkdir -p $subcorpus_out

    # loop through all cha files
    for f in $subcorpus_in/*.cha; do
	# Notice there is a subselection - only docs with 1 adult are processed
        regexp='Sibl.+\|Broth.+\|Sist.+\|Target_.+\|Child\|To.+\|Environ.+\|Cousin\|Non_Hum.+\|Play.+'
        nadults=$(grep "@ID" < $f | grep -v -i $regexp | wc -l)

	if [ $nadults == 1 ];  then
	    selfile=$subcorpus_out/$(basename $f .cha)"-includedlines.txt"
	    $scriptdir/cha2sel.sh $f $selfile > /dev/null

	    ortho=$subcorpus_out/$(basename $f .cha)"-ortholines.txt"
	    $scriptdir/selcha2clean.sh $selfile $ortho > /dev/null
	    echo "processed $(basename $f)"
	fi
    done
done

# remove empty folders for non-processed corpora
#find $res_folder -type d -empty -delete
#echo "done removing empty folders"
