# -*- coding: utf-8 -*-
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
