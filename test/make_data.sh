#!/usr/bin/env bash
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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.


# Prepare 1% of the buckeye corpus as test data for abkhazia. Copy the
# data in ./data if not specified


# init an empty output data directory
data_dir=${1:-./data}
[ -e $data_dir ] && { echo "error: $data_dir already existing"; exit 1; }
mkdir $data_dir

# init an empty tmp directory, destroy it at exit
tmpdir=$(mktemp -d /tmp/data.XXXX)
trap "rm -rf $tmpdir" EXIT

# prepare 1% of buckeye in the data dircetory (random by utterances)
abkhazia prepare buckeye > /dev/null
abkhazia split buckeye -T 0.01 -o $tmpdir > /dev/null
mv $tmpdir/split/train/data/* $data_dir
