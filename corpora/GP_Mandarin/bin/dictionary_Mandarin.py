# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 22:33:43 2015

@author: Thomas Schatz
"""

import tempfile
import codecs
import os
import logging

logger = logging.getLogger('Mandarin')

def correct_dictionary(dictionary_file):
	"""
	script to correct problems with the original Global Phone Mandarin dictionary
	the corrections are completely ad hoc
	the result is stored in a temporary file
	"""
	logger.info("Correcting dictionary")
	# the following words are in the dictionary but are not used in the transcriptions
	# they will be dropped
	words_to_drop = [u"#fragment#", u"#noise#", u"$", u"(", u")", u"SIL"]
	# read input file
	with codecs.open(dictionary_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	# correct content
	correct_lines = []
	for line in lines:
		if all([not(u"{"+word+u"}" in line) for word in words_to_drop]):
			if u"{lai2zhe3bu2ju4 }" in line:
				line = line.replace(u"{lai2zhe3bu2ju4 }", u"{lai2zhe3bu2ju4}")
			correct_lines.append(line)
	# generate output file
	fid, filename = tempfile.mkstemp()
	os.close(fid)
	with codecs.open(filename, mode='w', encoding='UTF-8') as out:
		for line in correct_lines:
			out.write(line)
	logger.info("Dictionary corrected")
	return filename