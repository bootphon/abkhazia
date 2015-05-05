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

# This is a simple kaldi recipe for use with the abkhazia library
# (a library to perform ABX and kaldi experiments on speech corpora
# in a unified and easy way, see: https://github.com/bootphon/abkhazia)
# Its main object are to:
#  - train a GMM-HMM model with triphone word-position-dependent states 
# and speaker adaptation using a dedicated training set
#  - train a bigram word model on the same training set
#  - Put these model together to decode a test set and extract Viterbi-style
# posteriorgrams from the resulting lattices

###### Parameters ######

# do all computation or focus on main ones
decode_train=false
skip_training=false
# feature parameters
use_pitch=true
# speaker-independent triphone models parameters:
num_states_si=2500
num_gauss_si=15000
# speaker-adaptive triphone models parameters:
num_states_sa=2500
num_gauss_sa=15000
# location of the language model to be used:
lm=data/lang_test
lm_name=lm


###### Recipe ######

[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

if [ "$skip_training" = false ] ; then
  # First finish preparing data
  utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
  utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
  utils/prepare_lang.sh --position-dependent-phones true \
      data/local/dict "<unk>" data/local/lang_tmp data/lang \
      >& data/prepare_lang.log

  # Features
  mfccdir=mfcc
  if [ "$use_pitch" = true ] ; then
    make_feats="steps/make_mfcc_pitch.sh"
  else
    make_feats="steps/make_mfcc.sh"
  fi
  for x in train test; do 
    ( 
      $make_feats --nj 20 --cmd "$train_cmd" data/$x \
  exp/make_mfcc/$x $mfccdir;
      steps/compute_cmvn_stats.sh data/$x exp/make_mfcc/$x $mfccdir; 
    ) &
  done
  wait;

  # Monophone model training
  mkdir -p exp/mono;
  steps/train_mono.sh --nj 8 --cmd "$train_cmd" \
    data/train data/lang exp/mono > exp/mono/train.log
fi

# Monophone model test 
# done in parallel from next training steps
(
  # first instantiate full decoding graph (HCLG)
  decode_dir=exp/mono/$lm_name
  mkdir -p $decode_dir
  graph_dir=$decode_dir/graph
  mkdir -p $graph_dir
  $highmem_cmd $graph_dir/mkgraph.log \
    utils/mkgraph.sh --mono $lm exp/mono \
    $graph_dir
  # decode and compute WER on test set
  steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/test \
    $decode_dir/decode_test
  # if full computations: decode and compute WER on train set too
  if [ "$decode_train" = true ] ; then
    steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/train \
      $decode_dir/decode_train
  fi
)&

# Triphone model training 
if [ "$skip_training" = false ] ; then
  # first: forced alignment of train set with monophone model
  mkdir -p exp/mono_ali
  steps/align_si.sh --nj 8 --cmd "$train_cmd" \
    data/train data/lang exp/mono exp/mono_ali \
    > exp/mono_ali/align.log 
  # second: triphone model training
  mkdir -p exp/tri1
  steps/train_deltas.sh --cmd "$train_cmd" \
    $num_states_si $num_gauss_si data/train data/lang exp/mono_ali \
    exp/tri1 > exp/tri1/train.log
fi

# Triphone model test
# done in parallel from next training steps
(
  # instantiate full decoding graph (HCLG)
  decode_dir=exp/tri1/$lm_name
  mkdir -p $decode_dir
  graph_dir=$decode_dir/graph
  mkdir -p $graph_dir
  $highmem_cmd $graph_dir/mkgraph.log \
	utils/mkgraph.sh $lm exp/tri1 $graph_dir
  # decode and compute WER on test
  steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/test \
    $decode_dir/decode_test 
  # if full computations: decode and compute WER on train set too
  if [ "$decode_train" = true ] ; then
    steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/train \
	    $decode_dir/decode_train
  fi
)&

# Speaker adaptive triphone model training
if [ "$skip_training" = false ] ; then
  # forced alignment with fmllr based on speaker independent triphone model
  mkdir -p exp/tri1_ali_fmllr
  steps/align_fmllr.sh --nj 8 --cmd "$train_cmd" \
    data/train data/lang exp/tri1 exp/tri1_ali_fmllr \
    > exp/tri1_ali_fmllr/align.log
  # speaker adaptive training
  mkdir -p exp/tri2a
  steps/train_sat.sh --cmd "$train_cmd" \
    $num_states_sa $num_gauss_sa data/train data/lang exp/tri1_ali_fmllr \
    exp/tri2a > exp/tri2a/train.log
fi

# Speaker adaptive triphone model test 
# instantiate full decoding graph (HCLG)
# done in parallel from next training steps
(
  decode_dir=exp/tri2a/$lm_name
  mkdir -p $decode_dir
  graph_dir=$decode_dir/graph
  mkdir -p $graph_dir
  $highmem_cmd $graph_dir/mkgraph.log \
	utils/mkgraph.sh $lm exp/tri2a $graph_dir
  # decode and compute WER on test
  steps/decode_fmllr.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/test \
    $decode_dir/decode_test
  # if full computations: decode and compute WER on train set too
  if [ "$decode_train" = true ] ; then
    steps/decode_fmllr.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/train \
	    $decode_dir/decode_train
  fi
)&


##### Exporting results #####

mkdir -p export
# "lattice" Viterbi posteriors
lattice-to-post --acoustic-scale=0.1 "ark:gunzip -c exp/tri2a/decode_test/lat.*.gz|" ark,t:export/post.post
post-to-phone-post exp/tri2a/final.mdl ark,t:export/post.post ark,t:export/phone_post.post
## do we need to decode phone labels ?
# 1-best phone transcription, frame-by-frame (10.ali: lm weight, arbitrary choice)
ali-to-phones --per_frame=true exp/tri2a/final.mdl ark,t:exp/tri2a/decode_test/scoring/10.ali ark,t:export/best_transcript.tra
#utils/int2sym.pl -f 2- data/lang/phones.txt export/best_transcript.tra > export/best_transcript.txt

### Export formats ### 

# Posteriors: in export/phone_post.post
# posterior file format:
#   utt_id [frame_1] [frame_2] ... [frame_n]
# avec format pour frame_i:
#   phone_id_1 posterior_proba_1 phone_id_2 posterior_proba_2 ... phone_id_k posterior_proba_k
# note that not all phone_id are in each frame, those that aren't are supposed to be with
# posterior proba of 0.
# The correspondence between phones and phone-ids is given by the file:
#   data/lang/phones.txt
# note that it includes word-position variants of phones, I think it would be better
# to fold the variants of each phone together (just sum the corresponding posterior probas)
# before doing distance computations in ABX or STD.

# Phone transcription: in export/best_transcript.tra
# File format as for forced alignment, the correspondence between phones and phone-ids is given by the file:
# is also  data/lang/phones.txt

