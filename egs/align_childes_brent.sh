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

# This script computes force alignment (along with posterior
# probabilities) on the Brent subcorpus of the Childes database. The
# final alignment will be in the $data_dir/align/alignment.txt

data_dir=${1:-./align_childes_brent}
data_dir=$(readlink -f $data_dir)

echo 'preparing Brent corpus'
abkhazia prepare childes -o $data_dir || exit 1

echo 'computing MFCC features'
abkhazia features mfcc $data_dir --use-pitch true -v || exit 1

echo 'computing language model'
abkhazia language $data_dir -l word -n 2 -v || exit 1

echo 'computing acoustic model'
abkhazia acoustic $data_dir -t tri-sa -v || exit 1

echo 'computing forced alignment'
abkhazia align $data_dir --post --recipe -v || exit 1
