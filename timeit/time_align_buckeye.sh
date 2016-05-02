#!/bin/bash

data_dir=$1
data_dir=$(readlink -f $data_dir)

cfg=$2
[ ! -z $cfg ] && abkhazia="abkhazia -c $cfg" || abkhazia="abkhazia"

$abkhazia language $data_dir -l word -n 2 || exit 1
$abkhazia acoustic $data_dir -t tri-sa || exit 1
$abkhazia align $data_dir -j 4 || exit 1

echo 'symlink the result to $data_dir/forced_alignment.txt'
ln -s -f $data_dir/align/export/forced_alignment.txt $data_dir
