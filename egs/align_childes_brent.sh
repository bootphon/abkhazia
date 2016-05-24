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
# the $data_dir/split/train/align/export directory.

data_dir=${1:-./align_childes_brent_sub}
data_dir=$(readlink -f $data_dir)

#rm -rf $data_dir
# echo 'preparing Brent corpus'
# #abkhazia prepare childes -o $data_dir || exit 1
# abkhazia split -T 0.01 ./align_childes_brent -o $data_dir || exit 1
# exit 1

data_dir=$data_dir/split/train

echo 'computing MFCC features'
abkhazia features $data_dir --use-pitch true -v || exit 1

echo 'computing language model'
abkhazia language $data_dir -l word -n 2 -v || exit 1

echo 'computing acoustic model'
abkhazia acoustic $data_dir -t tri-sa -v || exit 1

# echo 'computing forced alignment'
# abkhazia align $train_dir --recipe || exit 1

# echo 'symlink the result to $data_dir/forced_alignment.txt'
# ln -s -f $train_dir/align/export/forced_alignment.txt $data_dir
