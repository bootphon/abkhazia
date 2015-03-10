# This contains the locations of the tools and data required for running
# the GlobalPhone experiments.

export LC_ALL=C  # For expected sorting and joining behaviour

KALDI_ROOT=/cm/shared/apps/kaldi

KALDISRC=$KALDI_ROOT/src
KALDIBIN=$KALDISRC/bin:$KALDISRC/featbin:$KALDISRC/fgmmbin:$KALDISRC/fstbin  
KALDIBIN=$KALDIBIN:$KALDISRC/gmmbin:$KALDISRC/latbin:$KALDISRC/nnetbin
KALDIBIN=$KALDIBIN:$KALDISRC/sgmmbin:$KALDISRC/lmbin:
KALDIBIN=$KALDIBIN:$KALDISRC/kwsbin:$KALDISRC/ivectorbin
KALDIBIN=$KALDIBIN:$KALDISRC/online2bin:$KALDISRC/sgmm2bin

FSTBIN=$KALDI_ROOT/tools/openfst/bin
LMBIN=$KALDI_ROOT/tools/irstlm/bin:$KALDI_ROOT/tools/srilm/bin/i686-m64
LMBIN=$LMBIN:$KALDI_ROOT/tools/srilm/bin/:$KALDI_ROOT/tools/sctk/bin/

[ -d $PWD/local ] || { echo "Error: 'local' subdirectory not found."; }
[ -d $PWD/utils ] || { echo "Error: 'utils' subdirectory not found."; }
[ -d $PWD/steps ] || { echo "Error: 'steps' subdirectory not found."; }

export kaldi_local=$PWD/local
export kaldi_utils=$PWD/utils
export kaldi_steps=$PWD/steps
SCRIPTS=$kaldi_local:$kaldi_utils:$kaldi_steps

export PATH=$PATH:$KALDIBIN:$FSTBIN:$LMBIN:$SCRIPTS
