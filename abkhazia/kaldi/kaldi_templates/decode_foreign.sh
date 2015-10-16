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

# Use a kaldi model to decode speech from a possibly different corpus possibly
# in a different language.
# This script assumes that there is a 'data/test' folder with already computed
# features in the foreign corpus (the features must be similar to those use to 
# train the kaldi model).
# It also assumes that a decoding graph has already been built for the model

# This script generates lattices, but it won't try to score them
# (it wouldn't make sense if the foreign corpus use a different lexicon or different
# phones, etc.)

###### Parameters ######

# if true also decode 'data/train' from the foreign corpus
decode_train=false
# used to decide whether to use 
# steps/decode.sh or steps/decode_fmllr.sh for decoding
fmllr_model=true

graph_dir="exp/tri2a/graph_phone_bigram"
# graph_dir="exp/tri2a/graph_phone_loop"
#foreign_recipe="../../../GP_Vietnamese/train_and_decode/s5"
# foreign_recipe="../../../CSJ_core_laymen/train_and_decode/s5"
foreign_recipe="../../../GP_Mandarin/train_and_decode/s5"
#output_test="exp/tri2a/decode_test_phone_bigram_GPV"
#output_train="exp/tri2a/decode_train_phone_bigram_GPV"
output_test="exp/tri2a/decode_test_phone_bigram_GPM"
output_train="exp/tri2a/decode_train_phone_bigram_GPM"
# output_test="exp/tri2a/decode_test_phone_loop_WSJ"
# output_train="exp/tri2a/decode_train_phone_loop_WSJ"


###### Recipe ######

[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

if [ "$fmllr_model" = true ] ; then
  decode_exe=steps/decode_fmllr.sh
else
  decode_exe=steps/decode.sh
fi

# decode test set
(
  $decode_exe --nj 8 --cmd "$decode_cmd" --skip_scoring true \
  $graph_dir "$foreign_recipe"/data/test $output_test
)&
if [ "$decode_train" = true ] ; then
  # decode train set
  $decode_exe --nj 8 --cmd "$decode_cmd" --skip_scoring true \
    $graph_dir "$foreign_recipe"/data/train $output_train
fi


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

