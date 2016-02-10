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


function failure {
    echo "Configuration failed !

$1

Please fix the problem and run this script again";
    exit 1;
}


# absolute path to the abkhazia setup directory
setupdir=`readlink -f .`

# path to the share directory in abkhazia
share=$setupdir/abkhazia/share


# Configuring abkhazia/share/abkhazia.cfg
conf=$share/abkhazia.cfg
if [ ! -e $conf ]; then
    # Init an empty configuration file if not existing
    echo "writing $conf"
    cat > $conf <<EOF
# This is the abkhazia configuration file. This file is automatically
# generated during installation. Change the values in here to overload
# the default configuration.

[abkhazia]
# The absolute path to the output data directory of abkhazia.
data-directory: $setupdir/data

[kaldi]
# The absolute path to the kaldi distribution directory
# YOU MUST SPECIFY THIS PATH MANUALLY. For exemple:
# kaldi-directory: /home/me/kaldi-trunk
kaldi-directory:
EOF
    failure "Please specify the path to the kaldi root directory in $conf"
else
    # check kaldi-dircetory is defined in the configuration file if existing
    kaldi=`cat $conf | sed '/^#/d' | grep kaldi-directory | cut -d: -f2 | sed 's/^ *//'`
    [ -z $kaldi ] &&
        failure "Please specify the path to the kaldi root directory in $conf"

    # check kaldi-directory is an existing directory
    [ -d $kaldi ] && echo "Found kaldi root directory as $kaldi" ||
            failure "Please correct the path to the kaldi root directory in
$conf
$kaldi is not an existing directory"

    # check sph2pipe is found in kaldi (also means kaldi is compiled)
    sph2pipe="$kaldi/tools/sph2pipe_v2.5/sph2pipe"
    [ -e $sph2pipe ] && echo "Found sph2pipe as $sph2pipe" ||
            failure "$sph2pipe not found in the kaldi distribution"
fi


# Download the CMU pronouncing dictionary if not present
cmu_url="http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict.0.7a"
cmu_dic=$share/`basename $cmu_url`
if [ -e $cmu_dic ]
then
    echo "Found CMU dictionary as $cmu_dic"
else
    echo "Downloading CMU dictionary from $cmu_url..."
    wget --quiet $cmu_url -O $cmu_dic || failure "Fail to download $cmu_url"
fi


# check sox is installed
sox=`which sox`
sox_failure="sox not found on your system, please install it (see http://sox.sourceforge.net)"
[ ! -z $sox ] && echo "Found sox as $sox" || failure "$sox_failure"

# check shorten is installed
shorten=`which shorten`
shorten_failure="shorten not found on your system, please install it from
http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz"
[ ! -z $shorten ] && echo "Found shorten as $shorten" || failure "$shorten_failure"

# check flac is installed
flac=`which flac`
flac_failure="flac not found on your system, please install it (see https://xiph.org/flac/)"
[ ! -z $flac ] && echo "Found flac as $flac" || failure "$flac_failure"

echo "
Configuration succeed ! To continue installation please type:
    python setup.py build
    python setup.py install"

exit 0
