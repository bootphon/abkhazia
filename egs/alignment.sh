#!/bin/bash
#
# Author: Mathieu Bernard
#
# This script takes a speech corpus in the abkhazia format and compute
# a forced alignment at phone level. This is simply a wrapper on
# abkhazia commands.
#
# TODO This have to be tested on a corpus!! e.g. buckeye

# Parameters
corpus=$1
output_dir=$2


#mkdir -p $output_dir || exit 1

# compute standard MFCC features with CMVN
#abkhazia features mfcc --verbose --h5f --cmvn -o $output_dir/features $corpus || exit 1

# compute a phone level trigram language model
#abkhazia language --verbose -n 3 -l phone -o $output_dir/language $corpus || exit 1

# train a speaker adaptive triphone acoustic model
abkhazia acoustic monophone --verbose $corpus -o $output_dir/am_mono \
         -l $output_dir/language -f $output_dir/features || exit 1

abkhazia acoustic triphone --vervose $corpus -o $output_dir/am_tri \
         -i $output_dir/am_mono -l $output_dir/language -f $output_dir/features || exit 1

abkhazia acoustic triphone-sa --vervose $corpus -o $output_dir/am_trisa \
         -i $output_dir/am_tri -l $output_dir/language -f $output_dir/features || exit 1

# compute the forced alignment
abkhazia align --verbose --phones-only $corpus -o $output_dir/alignment \
         -l $output_dir/language -a $output_dir/am_trisa -f $output_dir/features || exit 1
