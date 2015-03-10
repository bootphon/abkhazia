#!/bin/bash -u

# Copyright 2015 Thomas Schatz  
# adapted from Arnab Ghoshal recipe for the GlobalPhone corpus
#
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

echo "This shell script may run as-is on your system, but it is recommended 
that you run the commands one by one by copying and pasting into the shell."
#exit 1;

[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }


## the value of the following parameter was adjusted to control overfitting (see RESULTS file)
# speaker-independent triphone models parameters:
num_states_si=150
num_gauss_si=3000
# speaker-adaptive triphone models parameters:
num_states_sa=400
num_gauss_sa=10000
cluster_threshold=100

# First finish preparing data
utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
utils/prepare_lang.sh --position-dependent-phones true \
    data/local/dict "<UNK>" data/local/lang_tmp data/lang \
    >& data/prepare_lang.log


# Now make MFCC features
mfccdir=mfcc
for x in train test; do 
  ( 
    steps/make_mfcc.sh --nj 4 --cmd "$train_cmd" data/$x \
exp/make_mfcc/$x $mfccdir;
    steps/compute_cmvn_stats.sh data/$x exp/make_mfcc/$x $mfccdir; 
  ) &
done
wait;


# monophone model training
mkdir -p exp/mono;
steps/train_mono.sh --nj 4 --cmd "$train_cmd" \
  data/train data/lang exp/mono >& exp/mono/train.log &
wait;


# monophone model test (on both train and test sets to get an idea of overfitting magnitude)
# first compile decoding language model to binary openfst format and put it in data/lang
fstcompile --isymbols=data/lang/words.txt --osymbols=data/lang/words.txt --keep_isymbols=false \
    --keep_osymbols=false data/local/dict/G.txt > data/lang/G.fst
# then instantiate full decoding graph (HCLG)
graph_dir=exp/mono/graph
mkdir -p $graph_dir
$highmem_cmd $graph_dir/mkgraph.log \
  utils/mkgraph.sh --mono data/lang exp/mono \
  $graph_dir
# check out language model (G) graphically (this is not necessary, this is just for illustration purposes)
fstdraw --isymbols=data/lang/words.txt --osymbols=data/lang/words.txt data/lang/G.fst > data/lang/G.dot
dot -Tps data/lang/G.dot > data/lang/G.ps
# check out lexicon model (L) graphicallly (this is not necessary, this is just for illustration purposes)
fstdraw --isymbols=data/lang/phones.txt --osymbols=data/lang/words.txt data/lang/L.fst > data/lang/L.dot
dot -Tps data/lang/L.dot > data/lang/L.ps
# check language model composed with lexicon (LG) graphically (this is not necessary, this is just for illustration purposes)
fstdraw --isymbols=data/lang/phones.txt --osymbols=data/lang/words.txt data/lang/tmp/LG.fst > data/lang/tmp/LG.dot
dot -Tps data/lang/tmp/LG.dot > data/lang/tmp/LG.ps
# CLG and HCLG models could be checked out similarly
# decode and compute WER on train set
steps/decode.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/train \
  exp/mono/decode_train
# decode and compute WER on test set
steps/decode.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/test \
  exp/mono/decode_test


# triphone model training 
# first: forced alignment of train set with monophone model
mkdir -p exp/mono_ali
steps/align_si.sh --nj 4 --cmd "$train_cmd" \
  data/train data/lang exp/mono exp/mono_ali \
  >& exp/mono_ali/align.log 
# second: triphone model training
mkdir -p exp/tri1
steps/train_deltas.sh --cmd "$train_cmd" --cluster-thresh $cluster_threshold \
  $num_states_si $num_gauss_si data/train data/lang exp/mono_ali \
  exp/tri1 >& exp/tri1/train.log
wait;

mkdir -p exp/tri1_ali
steps/align_si.sh --nj 4 --cmd "$train_cmd" \
  data/train data/lang exp/tri1 exp/tri1_ali
mkdir -p exp/tri_lda_mllt
steps/train_lda_mllt.sh --cmd "$train_cmd" \
  --splice-opts "--left-context=3 --right-context=3" \
  --cluster-thresh $cluster_threshold $num_states_si $num_gauss_si \
  data/train data/lang exp/tri1_ali exp/tri_lda_mllt \
  > exp/tri_lda_mllt/train.log


# triphone model test (on both train and test sets to get an idea of overfitting magnitude)
# instantiate full decoding graph (HCLG)
graph_dir=exp/tri1/graph
mkdir -p $graph_dir
$highmem_cmd $graph_dir/mkgraph.log \
	utils/mkgraph.sh data/lang exp/tri1 $graph_dir
# decode and compute WER on train
steps/decode.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/train \
	exp/tri1/decode_train 
# decode and compute WER on test
steps/decode.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/test \
  exp/tri1/decode_test 

graph_dir=exp/tri_lda_mllt/graph
mkdir -p $graph_dir
$highmem_cmd $graph_dir/mkgraph.log \
  utils/mkgraph.sh data/lang exp/tri_lda_mllt $graph_dir
steps/decode.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/train \
  exp/tri_lda_mllt/decode_train
steps/decode.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/test \
  exp/tri_lda_mllt/decode_test  


# speaker adaptive triphone model training
# forced alignment with fmllr based on speaker independent triphone model
mkdir -p exp/tri1_ali_fmllr
steps/align_fmllr.sh --nj 4 --cmd "$train_cmd" \
  data/train data/lang exp/tri1 exp/tri1_ali_fmllr \
  >& exp/tri1_ali_fmllr/align.log  || exit 1;
# speaker adaptive training
mkdir -p exp/tri2a
steps/train_sat.sh --cmd "$train_cmd" --cluster-thresh $cluster_threshold \
  $num_states_sa $num_gauss_sa data/train data/lang exp/tri1_ali_fmllr \
  exp/tri2a >& exp/tri2a/train.log
wait;


# speaker adaptive triphone model test (on both train and test sets to get an idea of overfitting magnitude)
# instantiate full decoding graph (HCLG)
graph_dir=exp/tri2a/graph
mkdir -p $graph_dir
$highmem_cmd $graph_dir/mkgraph.log \
	utils/mkgraph.sh data/lang exp/tri2a $graph_dir
# decode and compute WER on train
steps/decode_fmllr.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/train \
	exp/tri2a/decode_train
# decode and compute WER on test
steps/decode_fmllr.sh --nj 4 --cmd "$decode_cmd" $graph_dir data/test \
  exp/tri2a/decode_test


## Examples of how to export different results files in human-readable format 
## that can be used by other programs

mkdir export

# 1. exporting a word transcription
utils/int2sym.pl -f 2- data/lang/words.txt exp/mono/decode_train/scoring/5.tra > export/word_trans_example.txt

# 2. exporting a phone-level alignment
ali-to-phones --per_frame=true exp/mono/final.mdl ark,t:exp/mono/decode_train/scoring/5.ali ark,t:export/phone_ali_example.tra
# options per_frame is false by default...
# note that the ark,t is very important for correct handling of the file (t for table format?)
utils/int2sym.pl -f 2- data/lang/phones.txt export/phone_ali_example.tra > export/phone_ali_example.txt

# 3. exporting a phone-level forced alignment
ali-to-phones --per_frame=true exp/mono_ali/final.mdl "ark,t:gunzip -c exp/mono_ali/ali.1.gz|" ark,t:export/forced_ali_example.tra
# options per_frame is false by default...
# note that the ark,t is very important for correct handling of the file (t for table format?)
utils/int2sym.pl -f 2- data/lang/phones.txt export/forced_ali_example.tra > export/forced_ali_example.txt
