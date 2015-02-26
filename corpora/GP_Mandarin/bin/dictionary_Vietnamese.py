# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 22:33:43 2015

@author: Thomas Schatz
"""

import tempfile
import codecs
import os
import re
import logging

# in the Vietnamese dictionary alternative pronunciations are supplied 
# for certain words, but they are not explicitly used in the text
# there are never more than two version of a given word

# for now we simply drop them

# note that kaldi can accomodate alternate pronunciation and even
# pronunciation probabilities without problems, but using them in ABX 
# would be bothersome

# one possibility to accomodate several pronunciation would be to have an 
# optional lexicon_with_variants.txt file, optionally also with probabilities
# that would be used by kaldi
# then one could either ignore the variants in ABX or use the kaldi acoustic models
# to do a hard assignment of each occurence of each word to a given pronunciation

# here we make the assumption that the first pronunciation (without the (2) suffix)
# is the more likely
# we could check this assumption by comparing WERs with first or second variant or both

logger = logging.getLogger('Vietnamese')


def correct_dictionary(dictionary_file):
	"""
	script to correct problems with the original Global Phone Vietnamese dictionary
	the corrections are completely ad hoc
	the result is stored in a temporary file
	"""
	logger.info("Correcting dictionary")
	# the following words are in the dictionary but are not used in the transcriptions
	# they will be dropped
	words_to_drop = [u"$", u"(", u")"]
	# read input file
	with codecs.open(dictionary_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	# correct content
	correct_lines = []
	for line in lines:
		if all([not(u"{"+word+u"}" in line) for word in words_to_drop]):
			# rewrite tone markers in a manner consistent
			# with GlobalPhone Mandarin pinyin markings
			if u"WB " in line:
				line = line.replace(u"WB ", u"WB")
			if u"  " in line:
				line = line.replace(u"  ", u" ")
			line = re.sub(u"\{(\w*) T(\d)\}", u"\\1_\\2", line)
			line = re.sub(u"\{(\w*) T(\d) WB\}", u"{\\1_\\2 WB}", line)
			correct_lines.append(line)
	# generate output file
	fid, filename = tempfile.mkstemp()
	os.close(fid)
	with codecs.open(filename, mode='w', encoding='UTF-8') as out:
		for line in correct_lines:
			out.write(line)
	logger.info("Dictionary corrected")
	return filename