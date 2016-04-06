#!/usr/bin/env bash
#
# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.


# called on kaldi building errors
function failure { [ ! -z "$1" ] && echo $1; exit 1; }

# number of CPU cores on the machine, to do parallel compilation
ncores=$(grep -c ^processor /proc/cpuinfo)

# absolute path to the kaldi directory (where it is/will be downloaded
# and compiled)
kaldi=${1:-./kaldi}
kaldi=$(readlink -f $kaldi)

# if the directory don't exist, clone our abkhazia kaldi fork in it,
# else fetch any new update.
if [ ! -d $kaldi ]
then
    git clone --branch abkhazia --single-branch \
        git@github.com:bootphon/kaldi.git $kaldi \
        || failure "failed to download kaldi from github"
else
    cd $kaldi
    git pull origin abkhazia || failure "failed to pull abkhazia branch"
    git checkout abkhazia || failure "failed to checkout to abkhazia branch"
fi

# From $kaldi/tools/extras/check_dependencies.sh. Debian systems
# generally link /bin/sh to dash, which doesn't work with some scripts
# as it doesn't expand x.{1,2}.y to x.1.y x.2.y
[ $(readlink /bin/sh) == "dash" ] && \
    failure  "failed because /bin/sh is linked to dash, and currently \
         some of the scripts will not run properly. We recommend to run: \
         sudo ln -s -f bash /bin/sh"

# compile kaldi tools
cd $kaldi/tools
./extras/check_dependencies.sh || failure "failed to check kaldi dependencies"
make -j $ncores || failure "failed to build kaldi tools"

# compile kaldi src
cd $kaldi/src
./configure --shared || failure "failed to configure kaldi"
# compile with optimizations and without debug symbols.
sed -i "s/\-g # -O0 -DKALDI_PARANOID.*$/-O3 -DNDEBUG/" kaldi.mk
make depend -j $ncores || failure "failed to setup kaldi dependencies"
make -j $ncores || failure "failed to build kaldi"



## TODO this is commented out since this is already checked in
## abkhazia configure script.
# # install SRILM
# cd $kaldi/tools
# if [ ! -d ./srilm ]; then
#     ./extras/install_srilm.sh || failure "failed to install SRILM"
# fi

# # install IRSTLM
# if [ ! -d ./irstlm ]; then
#     ./extras/install_irstlm.sh || failure "failed to install IRSTLM"
# fi
