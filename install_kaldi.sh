#!/usr/bin/env bash
#
# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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


# equivalent to $(readlink -f $1) but in pure bash (compatible with
# mac OS)
function realpath {
    pushd `dirname $1` > /dev/null
    echo $(pwd -P)
    popd > /dev/null
}

# called on kaldi building errors
function failure { [ ! -z "$1" ] && echo $1; exit 1; }

# number of CPU cores on the machine, to do parallel compilation
if [ $(uname) == 'Darwin' ]; then
    ncores=$(sysctl -a | grep machdep.cpu.core_count | cut -d: -f2 | tr -d ' ')
else
    ncores=$(grep -c ^processor /proc/cpuinfo)
fi

# absolute path to the kaldi directory (where it is/will be downloaded
# and compiled)
kaldi=${1:-./kaldi}

# if the directory don't exist, clone our abkhazia kaldi fork in it,
# else fetch any new update.
if [ ! -d $kaldi ]
then
    git clone --branch abkhazia --single-branch \
        https://github.com/bootphon/kaldi.git $kaldi \
        || failure "failed to download kaldi from github"
else
    cd $kaldi
    git pull origin abkhazia || failure "failed to pull abkhazia branch"
    git checkout abkhazia || failure "failed to checkout to abkhazia branch"
fi
kaldi=$(realpath $kaldi/src)

# From $kaldi/tools/extras/check_dependencies.sh. Debian systems
# generally link /bin/sh to dash, which doesn't work with some scripts
# as it doesn't expand x.{1,2}.y to x.1.y x.2.y
[ $(realpath /bin/sh) == "/bin/dash" ] && \
    failure  "failed because /bin/sh is linked to dash, and currently \
         some of the scripts will not run properly. We recommend to run: \
         sudo ln -s -f bash /bin/sh"

# compile kaldi tools
cd $kaldi/tools
./extras/check_dependencies.sh || failure "failed to check kaldi dependencies"
make -j $ncores || failure "failed to build kaldi tools"
./extras/install_openblas.sh || failure "failed to install openblas"

# compile kaldi src
cd $kaldi/src
./configure --openblas-root=../tools/OpenBLAS/install \
    || failure "failed to configure kaldi"
# compile with optimizations and without debug symbols.
sed -i "s/\-g # -O0 -DKALDI_PARANOID.*$/-O3 -DNDEBUG/" kaldi.mk
# use clang instead of gcc
sed -i "s/ -rdynamic//g" kaldi.mk
sed -i "s/g++/clang++/" kaldi.mk
make depend -j $ncores || failure "failed to setup kaldi dependencies"
make -j $ncores || failure "failed to build kaldi"

# compile irstlm
cd $kaldi/tools/extras
rm -f install_irstlm.sh
wget https://raw.githubusercontent.com/kaldi-asr/kaldi/master/tools/extras/install_irstlm.sh
wget https://raw.githubusercontent.com/kaldi-asr/kaldi/master/tools/extras/irstlm.patch
cd $kaldi/tools
./extras/install_irstlm.sh || failure "failed to install IRSTLM"

# forward the path to Kaldi to the configure script
export KALDI_PATH=$kaldi
