#!/bin/bash -u
# Copyright 2015, 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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

# This script manages the automatic download, configuration and
# compilation of kaldi from its official github repository

share=$(readlink -f .)

# Where to install kaldi (read from configuration file)
kaldi_dir=$(sed '/^#/d' $share/abkhazia.cfg | grep kaldi-directory | cut -d: -f2)

# Look if there is an existing kaldi in it


echo $kaldi_dir
