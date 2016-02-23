#!/bin/bash -u
# Copyright 2015, 2016  Thomas Schatz
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

# This is a simple kaldi recipe for use with the abkhazia library.
# Its main object is to:
#
# - train a GMM-HMM model with triphone word-position-dependent states
#   and speaker adaptation on a whole corpus
#
# - output a forced time-alignment at the phone-level for the whole
#   corpus

###### Parameters ######

# do all computation or focus on main ones
optional_silence=true

# feature parameters
use_pitch=true

# speaker-independent triphone models parameters
num_states_si=2500
num_gauss_si=15000

# speaker-adaptive triphone models parameters
num_states_sa=2500
num_gauss_sa=15000


###### Recipe ######

[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

# First finish preparing data
utils/utt2spk_to_spk2utt.pl data/main/utt2spk > data/main/spk2utt
if [ "$optional_silence" = true ] ; then
  sil_prob=0.5
else
  sil_prob=0.0
fi
utils/prepare_lang.sh \
  --position-dependent-phones true \
  --sil_prob $sil_prob \
  data/local/dict "<unk>" data/local/lang_tmp data/lang \
  >& data/prepare_lang.log

# Features
mfccdir=mfcc
if [ "$use_pitch" = true ] ; then
  make_feats="steps/make_mfcc_pitch.sh"
else
  make_feats="steps/make_mfcc.sh"
fi
for x in main; do
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
  data/main data/lang exp/mono > exp/mono/train.log

# Triphone model training
# first: forced alignment of train set with monophone model
mkdir -p exp/mono_ali
steps/align_si.sh --nj 8 --cmd "$train_cmd" \
  data/main data/lang exp/mono exp/mono_ali \
  > exp/mono_ali/align.log
# second: triphone model training
mkdir -p exp/tri1
steps/train_deltas.sh --cmd "$train_cmd" \
  $num_states_si $num_gauss_si data/main data/lang exp/mono_ali \
  exp/tri1 > exp/tri1/train.log

# Speaker adaptive triphone model training
# first: forced alignment with fmllr based on speaker independent triphone model
mkdir -p exp/tri1_ali_fmllr
steps/align_fmllr.sh --nj 8 --cmd "$train_cmd" \
  data/main data/lang exp/tri1 exp/tri1_ali_fmllr \
  > exp/tri1_ali_fmllr/align.log
# second: speaker adaptive training
mkdir -p exp/tri2a
steps/train_sat.sh --cmd "$train_cmd" \
  $num_states_sa $num_gauss_sa data/main data/lang exp/tri1_ali_fmllr \
  exp/tri2a > exp/tri2a/train.log

# Final forced alignment
mkdir -p exp/tri2a_ali_fmllr
steps/align_fmllr.sh --nj 1 --cmd "$train_cmd" \
  data/main data/lang exp/tri2a exp/tri2a_ali_fmllr \
  >& exp/tri2a_ali_fmllr/align.log

##### Exporting results #####
mkdir -p export
ali-to-phones --write_lengths=true exp/tri2a/final.mdl \
              "ark,t:gunzip -c exp/tri2a_ali_fmllr/ali.1.gz|" \
              ark,t:export/forced_alignment.tra

# if we want to use the tri2a results directly without the final forced alignment
# (is there any difference between the two beyond one being done using only one job?)
# ali-to-phones --write_lengths=true exp/tri2a/final.mdl "ark,t:gunzip -c exp/tri2a/ali.*.gz|" ark,t:export/forced_alignment.tra
