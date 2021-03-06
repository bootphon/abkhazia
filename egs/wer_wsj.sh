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


# This script compute Word Error Rate on the Wall Street Journal
# corpus. The 4 acoustic models in the pipeline are evaluated (mono,
# tri, tri-sa and dnn). Only Journalist Read selection, about 4h for
# train, 4h for test (10 speakers each)

data_dir=${1:-/home/mbernard/scratch/data/abkhazia/wsj}
data_dir=$(readlink -f $data_dir)

echo 'preparing WSJ (journalist read only)'
abkhazia prepare wsj --selection 1 --verbose -o $data_dir || exit 1

echo 'split in train and test subcorpora (50% each, by speaker)'
abkhazia split -t 0.5 -b -v $data_dir || exit 1
train_dir=$data_dir/split/train
test_dir=$data_dir/split/test

echo 'computing MFCC features and word bigram for train set'
abkhazia features mfcc $train_dir --pitch --cmvn -v || exit 1
abkhazia language $train_dir -l word -n 2 -v || exit 1

echo 'computing MFCC features and word bigram for test set'
abkhazia features mfcc $test_dir --pitch --cmvn -v || exit 1
abkhazia language $test_dir -l word -n 2 -v || exit 1

echo 'computing monophone model'
abkhazia acoustic monophone -v $train_dir || exit 1

echo 'computing triphone model'
abkhazia acoustic triphone -v -i $train_dir/monophone $train_dir || exit 1

echo 'computing triphone-sa model'
abkhazia acoustic triphone-sa -v -i $train_dir/triphone $train_dir || exit 1

echo 'computing DNN model'
abkhazia acoustic nnet --force --recipe -v -i $train_dir/triphone-sa $train_dir || exit 1


echo 'decoding monophone model'
abkhazia decode si $test_dir -o $test_dir/decode_monophone --recipe --force -v \
         -a $train_dir/monophone -l $train_dir/language || exit 1

echo 'decoding triphone model'
abkhazia decode si $test_dir -o $test_dir/decode_triphone --recipe --force -v \
         -a $train_dir/triphone -l $train_dir/language || exit 1

echo 'decoding triphone-sa model'
abkhazia decode sa $test_dir -o $test_dir/decode_triphone-sa --recipe --force -v \
         -a $train_dir/triphone-sa -l $train_dir/language || exit 1

echo 'aligning tri-sa model'
abkhazia align --recipe --force --verbose --post $test_dir -o $test_dir/align_trisa \
         -a $train_dir/triphone-sa -l $train_dir/language || exit 1

echo 'decoding DNN model'
abkhazia decode nnet $test_dir -o $test_dir/decode_nnet --recipe --force -v \
         -a $train_dir/nnet -l $train_dir/language || exit 1
#        --transform-dir $test_dir/decode_triphone-sa || exit 1

exit 0
