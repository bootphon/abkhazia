# -*- coding: utf-8 -*-
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

"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""
import argparse


def extract_stats(corpus_path, verbose=False):
	pass


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=\
		(
		"extracts standard statistics "
		"from a corpus formatted for use with the abkhazia library"
		)
	)
	parser.add_argument('corpus_path', help=\
		(
		"path to the folder containing the corpus "
		"in abkhazia format"
		)
	)
	parser.add_argument('--verbose', action='store_true', help='verbose flag')
	args = parser.parse_args()
	extract_stats(args.corpus_path, args.verbose)
