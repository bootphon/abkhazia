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


# This script compute Phone Error Rate on the WSJ corpus.

data_dir=${1:-/home/mbernard/scratch/data/abkhazia/wsj_per}
data_dir=$(readlink -f $data_dir)

echo 'preparing WSJ (journalist read only)'
abkhazia prepare wsj --selection 1 --verbose -o $data_dir \
         /fhgfs/bootphon/data/raw_data/WSJ_LDC/ || exit 1

echo 'split in train and test subcorpora (50% each, by speaker)'
abkhazia split -t 0.5 -b -v $data_dir || exit 1
train_dir=$data_dir/split/train
test_dir=$data_dir/split/test

echo 'computing MFCC features and phone bigram for train set'
abkhazia features mfcc $train_dir --cmvn --force -v || exit 1
abkhazia language $train_dir -l phone -n 2 --force -v || exit 1

echo 'computing monophone model'
abkhazia acoustic monophone --verbose --force --recipe $train_dir || exit 1

echo 'decoding monophone model'
abkhazia features mfcc $test_dir --cmvn --force -v || exit 1
abkhazia decode si $test_dir -o $test_dir/decode_monophone --recipe --force -v \
         -a $train_dir/monophone -l $train_dir/language || exit 1
