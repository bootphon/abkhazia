[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

## the value of the following parameter was adjusted to control overfitting (see RESULTS file)
# speaker-independent triphone models parameters:
num_states_si=2500
num_gauss_si=15000
# speaker-adaptive triphone models parameters:
num_states_sa=2500
num_gauss_sa=15000

# First finish preparing data
utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
utils/prepare_lang.sh --position-dependent-phones true \
    data/local/dict "<unk>" data/local/lang_tmp data/lang \
    >& data/prepare_lang.log

# bigram LM training
lm=data/local/lm/train.arpa.gz
add-start-end.sh < data/local/lm/train_lm.txt > data/local/lm/train_lm_se.txt
build-lm.sh -i data/local/lm/train_lm_se.txt -n 2 -o data/local/lm/train.ilm.gz -k 1 -s kneser-ney
compile-lm data/local/lm/train.ilm.gz --text=yes /dev/stdout | gzip -c > $lm
rm data/local/lm/train.ilm.gz
# to get perplexity on test set:
# add-start-end.sh < data/local/lm/test_lm.txt > data/local/lm/test_lm_se.txt
# compile-lm $lm --eval=data/local/lm/test_lm_se.txt
# format LM in FST format
utils/format_lm_sri.sh data/lang $lm data/local/dict/lexicon.txt data/lang_test

# MFCC
mfccdir=mfcc
for x in train test; do 
  ( 
    steps/make_mfcc.sh --nj 20 --cmd "$train_cmd" data/$x \
exp/make_mfcc/$x $mfccdir;
    steps/compute_cmvn_stats.sh data/$x exp/make_mfcc/$x $mfccdir; 
  ) &
done
wait;

# keep this or filter wavefiles that are too short beforehand?
utils/fix_data_dir.sh data/train
utils/fix_data_dir.sh data/test

# monophone model training
mkdir -p exp/mono;
steps/train_mono.sh --nj 8 --cmd "$train_cmd" \
  data/train data/lang exp/mono > exp/mono/train.log

# monophone model test (on both train and test sets to get an idea of overfitting magnitude)
# done in parallel from next training steps
(
  # first instantiate full decoding graph (HCLG)
  graph_dir=exp/mono/graph
  mkdir -p $graph_dir
  $highmem_cmd $graph_dir/mkgraph.log \
    utils/mkgraph.sh --mono data/lang_test exp/mono \
    $graph_dir
  # decode and compute WER on test set
  steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/test \
    exp/mono/decode_test
  # decode and compute WER on train set
  steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/train \
    exp/mono/decode_train
)&

# triphone model training 
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


# triphone model test (on both train and test sets to get an idea of overfitting magnitude)
# done in parallel from next training steps
(
  # instantiate full decoding graph (HCLG)
  graph_dir=exp/tri1/graph
  mkdir -p $graph_dir
  $highmem_cmd $graph_dir/mkgraph.log \
	utils/mkgraph.sh data/lang_test exp/tri1 $graph_dir
  # decode and compute WER on test
  steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/test \
    exp/tri1/decode_test 
  # decode and compute WER on train
  steps/decode.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/train \
	exp/tri1/decode_train 
)&


# speaker adaptive triphone model training
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


# speaker adaptive triphone model test (on both train and test sets to get an idea of overfitting magnitude)
# instantiate full decoding graph (HCLG)
# done in parallel from next training steps
(
  graph_dir=exp/tri2a/graph
  mkdir -p $graph_dir
  $highmem_cmd $graph_dir/mkgraph.log \
	utils/mkgraph.sh data/lang_test exp/tri2a $graph_dir
  # decode and compute WER on test
  steps/decode_fmllr.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/test \
    exp/tri2a/decode_test
  # decode and compute WER on train
  steps/decode_fmllr.sh --nj 8 --cmd "$decode_cmd" $graph_dir data/train \
	exp/tri2a/decode_train
)&

# exporting results
mkdir -p export
# "lattice" Viterbi posteriors
lattice-to-post --acoustic-scale=0.1 "ark:gunzip -c exp/tri2a/decode_test/lat.*.gz|" ark,t:export/post.post
post-to-phone-post exp/tri2a/final.mdl ark,t:export/post.post ark,t:export/phone_post.post
## do we need to decode phone labels ?
# 1-best phone transcription, frame-by-frame (10.ali: lm weight, arbitrary choice)
ali-to-phones --per_frame=true exp/tri2a/final.mdl ark,t:exp/tri2a/decode_test/scoring/10.ali ark,t:export/best_transcript.tra
#utils/int2sym.pl -f 2- data/lang/phones.txt export/best_transcript.tra > export/best_transcript.txt


# Root of recipes:
#   - /fhgfs/bootphon/scratch/thomas/abkhazia/kaldi/Buckeye/train_and_decode/s5
#   - /fhgfs/bootphon/scratch/thomas/abkhazia/kaldi/NCHLT_Tsonga/train_and_decode/s5

#Posteriors: in export/phone_post.post
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

#Phone transcription: in export/best_transcript.tra
# File format as for forced alignment, the correspondence between phones and phone-ids is given by the file:
# is also  data/lang/phones.txt


