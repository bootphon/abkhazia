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

# This script computes force alignment (along with posterior
# probabilities) on the Brent subcorpus of the Childes database. The
# final alignment will be in the $data_dir/align/alignment.txt

data_dir=${1:-./align_childes_brent_1percent}
rm -rf $data_dir

function run {
    echo ;
    echo "************************************";
    echo "***  $1";
    echo "***  $2";
    echo "************************************";
    echo ;
    $2 || exit 1;
    read -p "Hit ENTER to continue";
}

cmd="abkhazia prepare childes -o $data_dir -v"
run "preparing Brent corpus" "$cmd"

cmd="abkhazia split -T 0.01 $data_dir -v"
run "select 1% of the corpus" "$cmd"
data_dir=$data_dir/split/train

cmd="abkhazia features mfcc $data_dir --use-pitch true -v"
run "computing MFCC features" "$cmd"

cmd="abkhazia language $data_dir -l word -n 2 -v"
run "computing language model" "$cmd"

cmd="abkhazia acoustic $data_dir -t tri-sa -v"
run "computing acoustic model" "$cmd"

cmd="abkhazia align $data_dir --post --recipe -v"
run "computing forced alignment" "$cmd"
