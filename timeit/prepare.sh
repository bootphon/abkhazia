#!/bin/bash

data_dir=$1
cfg=$2

[ ! -z $cfg ] && abkhazia="abkhazia -c $cfg" || abkhazia="abkhazia"

$abkhazia prepare buckeye --copy-wavs -o $data_dir || exit 1
$abkhazia split $data_dir -T 0.05 -f || exit 1

echo $data_dir/split/train
