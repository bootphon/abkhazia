#!/bin/bash -u

# Copyright 2015  Thomas Schatz

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
# WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
# See the Apache 2 License for the specific language governing permissions and
# limitations under the License.

# Estimates a simple N-gram language model

# Doesn't do anything specific to avoid overfitting
# if this become a problem, could use pruning:
#   prune-lm --threshold=1e-7 "$out_dir"/train.lm.gz "$out_dir"/train.plm
#   compile-lm "$out_dir"/train.plm --eval="$out_dir"/test_se
# (it's possible to specify different thresholds for the different n-gram levels)


###### Parameters ######
# for standard kaldi text files where format of each line: utt-id word1 word2 ...
remove_first_col=true
# text file from which to estimate the language model
train_file=$1
# folder in which to put the resulting FST
out_dir=$2
# text file on which to test the language model to estimate its perplexity
# if you don't have one, just pass the training file again, but be aware
# that the perplexity will be systematically underestimated in this case
test_file=$3
# n in n-gram
model_order=2


###### Recipe ######

[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

# train (use IRSTLM)
if [ $remove_first_col = true ]; then
  set -eu  # stop on error
  cut -d' ' -f2- < $train_file > "$out_dir"/train
else
  mv $train_file "$out_dir"/train
fi
add-start-end.sh < "$out_dir"/train > "$out_dir"/train_se
# k option is number of split, useful for huge text files
build-lm.sh -i "$out_dir"/train_se -n $model_order -o "$out_dir"/train.ilm.gz -k 1 -s kneser-ney
compile-lm train.ilm.gz --text=yes /dev/stdout | gzip -c > "$out_dir"/train.arpa.gz

# test (use IRSTLM)
if [ $remove_first_col = true ]; then
  set -eu # stop on error
  cut -d' ' -f2- < $test_file > "$out_dir"/test
else
  mv $test_file "$out_dir"/test
fi
add-start-end.sh < "$out_dir"/test > "$out_dir"/test_se
compile-lm "$out_dir"/train.arpa.gz --eval="$out_dir"/test_se

# generate FST (use SRILM)
utils/format_lm_sri.sh data/lang "$out_dir"/train.arpa.gz data/local/dict/lexicon.txt $out_dir

# clean
rm "$out_dir"/train
rm "$out_dir"/train_se
rm "$out_dir"/train.ilm.gz
rm "$out_dir"/train.arpa.gz
rm "$out_dir"/test
rm "$out_dir"/test_se
