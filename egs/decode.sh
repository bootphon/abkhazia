#!/bin/bash
# Copyright 2015, 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.


# This exemple shows how to train a full ASR model and decode some
# speech on it.

# prepare the output directory
data_dir=${1:-./data_decode_buckeye}
data_dir=$(readlink -f $data_dir)
train_dir=$data_dir/split/train
test_dir=$data_dir/split/test

# restart from scratch
rm -rf $data_dir
mkdir -p $data_dir

# corpus preparation. Here we assume you have a raw buckeye
# distribution and the 'buckeye-directory' is set in the abkhazia
# configuration file.
abkhazia prepare buckeye -v -o $data_dir || exit 1

# split in train and test sets (different speakers in each set)
abkhazia split -v --by-speakers --train 0.01 --test 0.01 $data_dir || exit 1

# compute MFCC features on test and train
abkhazia features mfcc $train_dir --cmvn -v || exit 1
abkhazia features mfcc $test_dir --cmvn -v || exit 1

abkhazia acoustic monophone -v $train_dir --recipe || exit 1

abkhazia language -n 2 -l word -v --recipe $test_dir

abkhazia decode si --recipe --verbose $test_dir \
         -a $train_dir/monophone \
         -l $test_dir/language -f $test_dir/features
