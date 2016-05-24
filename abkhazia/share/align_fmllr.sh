#!/bin/bash
# Copyright 2016  Mathieu Bernard
# Copyright 2012  Johns Hopkins University (Author: Daniel Povey)
# Apache 2.0

# Computes training alignments; assumes features are (LDA+MLLT or delta+delta-delta)
# + fMLLR (probably with SAT models).
# It first computes an alignment with the final.alimdl (or the final.mdl if final.alimdl
# is not present), then does 2 iterations of fMLLR estimation.

# If you supply the --use-graphs option, it will use the training
# graphs from the source directory (where the model is).  In this
# case the number of jobs must match the source directory.


# Begin configuration section.
stage=0
nj=4
cmd=run.pl
use_graphs=false
# Begin configuration.
scale_opts="--transition-scale=1.0 --acoustic-scale=0.1 --self-loop-scale=0.1"
acoustic_scale=0.1
lm_scale=0.1  # lattice-to-post parameter (default is 1)
beam=10
retry_beam=40
final_beam=20  # For the lattice-generation phase there is no retry-beam.  This
               # is a limitation of gmm-latgen-faster.  We just use an
               # intermediate beam.  We'll lose a little data and it will be
               # slightly slower.  (however, the min-active of 200 that
               # gmm-latgen-faster defaults to may help.)
careful=false
boost_silence=1.0 # factor by which to boost silence during alignment.
fmllr_update_type=full
# End configuration options.

#echo "$0 $@"  # Print the command line for logging

[ -f path.sh ] && . ./path.sh # source the path.
. parse_options.sh || exit 1;

if [ $# != 4 ]; then
   echo "usage: steps/align_fmllr.sh <data-dir> <lang-dir> <src-dir> <align-dir>"
   echo "e.g.:  steps/align_fmllr.sh data/train data/lang exp/tri1 exp/tri1_ali"
   echo "main options (for others, see top of script file)"
   echo "  --config <config-file>                           # config containing options"
   echo "  --nj <nj>                                        # number of parallel jobs"
   echo "  --use-graphs true                                # use graphs in src-dir"
   echo "  --cmd (utils/run.pl|utils/queue.pl <queue opts>) # how to run jobs."
   echo "  --fmllr-update-type (full|diag|offset|none)      # default full."
   exit 1;
fi

data=$1
lang=$2
srcdir=$3
dir=$4

oov=`cat $lang/oov.int` || exit 1;
silphonelist=`cat $lang/phones/silence.csl` || exit 1;
sdata=$data/split$nj

mkdir -p $dir/log
echo $nj > $dir/num_jobs
[[ -d $sdata && $data/feats.scp -ot $sdata ]] || split_data.sh $data $nj || exit 1;

cp $srcdir/{tree,final.mdl} $dir || exit 1;
cp $srcdir/final.alimdl $dir 2>/dev/null
cp $srcdir/final.occs $dir;
splice_opts=`cat $srcdir/splice_opts 2>/dev/null` # frame-splicing options.
cp $srcdir/splice_opts $dir 2>/dev/null # frame-splicing options.
cmvn_opts=`cat $srcdir/cmvn_opts 2>/dev/null`
cp $srcdir/cmvn_opts $dir 2>/dev/null # cmn/cmvn option.
delta_opts=`cat $srcdir/delta_opts 2>/dev/null`
cp $srcdir/delta_opts $dir 2>/dev/null

if [ -f $srcdir/final.mat ]; then feat_type=lda; else feat_type=delta; fi
echo "$0: feature type is $feat_type"

case $feat_type in
  delta) sifeats="ark,s,cs:apply-cmvn $cmvn_opts --utt2spk=ark:$sdata/JOB/utt2spk scp:$sdata/JOB/cmvn.scp scp:$sdata/JOB/feats.scp ark:- | add-deltas $delta_opts ark:- ark:- |";;
  lda) sifeats="ark,s,cs:apply-cmvn $cmvn_opts --utt2spk=ark:$sdata/JOB/utt2spk scp:$sdata/JOB/cmvn.scp scp:$sdata/JOB/feats.scp ark:- | splice-feats $splice_opts ark:- ark:- | transform-feats $srcdir/final.mat ark:- ark:- |"
    cp $srcdir/final.mat $dir
    cp $srcdir/full.mat $dir 2>/dev/null
   ;;
  *) echo "Invalid feature type $feat_type" && exit 1;
esac

## Set up model and alignment model.
mdl=$srcdir/final.mdl
if [ -f $srcdir/final.alimdl ]; then
  alimdl=$srcdir/final.alimdl
else
  alimdl=$srcdir/final.mdl
fi
[ ! -f $mdl ] && echo "$0: no such model $mdl" && exit 1;
alimdl_cmd="gmm-boost-silence --boost=$boost_silence `cat $lang/phones/optional_silence.csl` $alimdl - |"
mdl_cmd="gmm-boost-silence --boost=$boost_silence `cat $lang/phones/optional_silence.csl` $mdl - |"


## Work out where we're getting the graphs from.
if $use_graphs; then
  [ "$nj" != "`cat $srcdir/num_jobs`" ] && \
    echo "$0: you specified --use-graphs true, but #jobs mismatch." && exit 1;
  [ ! -f $srcdir/fsts.1.gz ] && echo "No graphs in $srcdir" && exit 1;
  graphdir=$srcdir
else
  graphdir=$dir
  if [ $stage -le 0 ]; then
    echo "$0: compiling training graphs"
    tra="ark:utils/sym2int.pl --map-oov $oov -f 2- $lang/words.txt $sdata/JOB/text|";
    $cmd JOB=1:$nj $dir/log/compile_graphs.JOB.log  \
      compile-train-graphs $dir/tree $dir/final.mdl  $lang/L.fst "$tra" \
        "ark:|gzip -c >$dir/fsts.JOB.gz" || exit 1;
  fi
fi


if [ $stage -le 1 ]; then
  echo "$0: aligning data in $data using $alimdl and speaker-independent features."
  $cmd JOB=1:$nj $dir/log/align_pass1.JOB.log \
    gmm-align-compiled $scale_opts --beam=$beam --retry-beam=$retry_beam --careful=$careful "$alimdl_cmd" \
    "ark:gunzip -c $graphdir/fsts.JOB.gz|" "$sifeats" "ark:|gzip -c >$dir/pre_ali.JOB.gz" || exit 1;
fi

if [ $stage -le 2 ]; then
  echo "$0: computing fMLLR transforms"
  if [ "$alimdl" != "$mdl" ]; then
    $cmd JOB=1:$nj $dir/log/fmllr.JOB.log \
      ali-to-post "ark:gunzip -c $dir/pre_ali.JOB.gz|" ark:- \| \
      weight-silence-post 0.0 $silphonelist $alimdl ark:- ark:- \| \
      gmm-post-to-gpost $alimdl "$sifeats" ark:- ark:- \| \
      gmm-est-fmllr-gpost --fmllr-update-type=$fmllr_update_type \
      --spk2utt=ark:$sdata/JOB/spk2utt $mdl "$sifeats" \
      ark,s,cs:- ark:$dir/trans.JOB || exit 1;
  else
    $cmd JOB=1:$nj $dir/log/fmllr.JOB.log \
      ali-to-post "ark:gunzip -c $dir/pre_ali.JOB.gz|" ark:- \| \
      weight-silence-post 0.0 $silphonelist $alimdl ark:- ark:- \| \
      gmm-est-fmllr --fmllr-update-type=$fmllr_update_type \
      --spk2utt=ark:$sdata/JOB/spk2utt $mdl "$sifeats" \
      ark,s,cs:- ark:$dir/trans.JOB || exit 1;
  fi
fi

feats="$sifeats transform-feats --utt2spk=ark:$sdata/JOB/utt2spk ark:$dir/trans.JOB ark:- ark:- |"

# if [ $stage -le 3 ]; then
#   echo "$0: doing final alignment."
#   $cmd JOB=1:$nj $dir/log/align_pass2.JOB.log \
#     gmm-align-compiled $scale_opts --beam=$beam --retry-beam=$retry_beam --careful=$careful "$mdl_cmd" \
#     "ark:gunzip -c $graphdir/fsts.JOB.gz|" "$feats" "ark:|gzip -c >$dir/ali.JOB.gz" || exit 1;

#   echo "$0: done aligning data."
# fi

# output the posterior probability of aligned utterances
if [ $stage -le 3 ]; then
  # Warning: gmm-latgen-faster doesn't support a retry-beam so you may get more
  # alignment errors (however, it does have a default min-active=200 so this
  # will tend to reduce alignment errors).
  # --allow_partial=false makes sure we reach the end of the decoding graph.
  # --word-determinize=false makes sure we retain the alternative pronunciations of
  #   words (including alternatives regarding optional silences).
  #  --lattice-beam=$beam keeps all the alternatives that were within the beam,
  #    it means we do no pruning of the lattice (lattices from a training transcription
  #    will be small anyway).
  echo "$0: generating lattice"
  $cmd JOB=1:$nj $dir/log/generate_lattices.JOB.log \
       gmm-latgen-faster --acoustic-scale=$acoustic_scale --beam=$final_beam \
       --lattice-beam=$final_beam --allow-partial=false --word-determinize=false \
       "$mdl_cmd" "ark:gunzip -c $dir/fsts.JOB.gz|" "$feats" "ark:|gzip -c >$dir/lat.JOB.gz" \
      || exit 1;

  echo "$0: computing phone level best path in lattice"
  $cmd JOB=1:$nj $dir/log/best_path.JOB.log \
       lattice-best-path --acoustic-scale=$acoustic_scale \
       "ark:gunzip -c $dir/lat.JOB.gz|" "ark:|gzip -c >$dir/tra.JOB.gz" \
       "ark:|gzip -c >$dir/best.JOB.gz" \
      || exit 1;

  $cmd JOB=1:$nj $dir/log/best_path.JOB.log \
       ali-to-phones --write_lengths=true $mdl "ark:gunzip -c $dir/best.JOB.gz|" \
       "ark,t:|gzip -c >$dir/ali.JOB.gz"

  $cmd JOB=1:$nj $dir/log/ali-to-phone.JOB.log \
       ali-to-phones --per-frame=true $mdl "ark:gunzip -c $dir/best.JOB.gz|" \
       "ark,t:|gzip -c >$dir/frame_ali.JOB.gz"

  echo "$0: generating phone posteriors on best path"
  $cmd JOB=1:$nj $dir/log/lattice-to-post.JOB.log \
       lattice-to-post --acoustic-scale=$acoustic_scale --lm-scale=$lm_scale \
       "ark:gunzip -c $dir/lat.JOB.gz|" ark:- \| \
       post-to-phone-post $mdl ark:- ark:- \| \
       get-post-on-ali ark:- "ark,t:gunzip -c $dir/frame_ali.JOB.gz|" \
       "ark,t:|gzip -c >$dir/post.JOB.gz" \
      || exit 1
fi

rm -f $dir/pre_ali.*.gz $dir/frame_ali.*.gz $dir/tra.*.gz $dir/best.*.gz

utils/summarize_warnings.pl $dir/log

exit 0;
