# This contains the locations of kaldi tools and data required for
# running the abkhazia recipes

export LC_ALL=C  # For expected sorting and joining behaviour

# This value is setup during abkhazia configuration
KALDI_ROOT=@kaldi-directory@

KALDISRC=$KALDI_ROOT/src
KALDIBIN=$KALDISRC/bin:$KALDISRC/featbin:$KALDISRC/fgmmbin:$KALDISRC/fstbin
KALDIBIN=$KALDIBIN:$KALDISRC/gmmbin:$KALDISRC/latbin:$KALDISRC/nnetbin
KALDIBIN=$KALDIBIN:$KALDISRC/sgmmbin:$KALDISRC/lmbin:
KALDIBIN=$KALDIBIN:$KALDISRC/kwsbin:$KALDISRC/ivectorbin
KALDIBIN=$KALDIBIN:$KALDISRC/online2bin:$KALDISRC/sgmm2bin

FSTBIN=$KALDI_ROOT/tools/openfst/bin

PLATFORM=i686-m64  # default path for Unix machines
[ $(uname) == "Darwin" ] && PLATFORM=macosx
LMBIN=$KALDI_ROOT/tools/irstlm/bin:$KALDI_ROOT/tools/srilm/bin/$PLATFORM
LMBIN=$LMBIN:$KALDI_ROOT/tools/srilm/bin/:$KALDI_ROOT/tools/sctk/bin/

#[ -d $PWD/local ] || { echo "$0: 'local' subdirectory not found."; }
[ -d $PWD/utils ] || { echo "$0: 'utils' subdirectory not found."; }
[ -d $PWD/steps ] || { echo "$0: 'steps' subdirectory not found."; }

export kaldi_local=$PWD/local
export kaldi_utils=$PWD/utils
export kaldi_steps=$PWD/steps
export IRSTLM=$KALDI_ROOT/tools/irstlm 	# for LM building
SCRIPTS=$kaldi_local:$kaldi_utils:$kaldi_steps

export PATH=$PATH:$KALDIBIN:$FSTBIN:$LMBIN:$SCRIPTS
