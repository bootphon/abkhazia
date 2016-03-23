#!/bin/bash
# Copyright 2015, 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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


# This exemple script computes force alignment of a subsample of the
# buckeye corpus. Writes to $data_dir, the final alignment will be in
# the $data_dir/split/train/align/s5/export directory.

data_dir=~/data/abkhazia/exemple
#rm -rf $data_dir

# Step 1 : prepare the corpus. Here we assume you have a raw buckeye
# distribution and the 'buckeye-directory' is set in the abkhazia
# configuration file.
abkhazia prepare buckeye -o $data_dir || exit 1

# Step 2 : split the prepared corpus in train and test sets. We keep
# only 5% for training and split by utterances.
abkhazia split $data_dir -T 0.05 -f || exit 1
train_dir=$data_dir/split/train

# Step 3 : compute a language model on the train set (a phone level
# bigram by default).
abkhazia language $train_dir --model-level word -f || exit 1

# Step 4 : compute an acoustic model on the train set (a speaker
# adapted triphone model by default).
abkhazia acoustic $train_dir -t mono -f -j 4 -k 4 || exit 1

# Step 5 : compute forced-alignment from the trained language and
# acoustic models.
abkhazia align $train_dir -vf -j 4 || exit 1

echo 'symlink the result to $data_dir/forced_alignment.txt'
ln -s -f $train_dir/align/s5/export/forced_alignment.txt $data_dir
