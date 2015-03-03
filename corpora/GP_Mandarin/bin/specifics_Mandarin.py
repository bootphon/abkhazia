# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 22:33:43 2015

@author: Thomas Schatz
"""
"""
Unresolved issues:
	speaker 84 all mixed up? utterance 10??? uterance 100??? and more?
	speaker 63 utterance 10????
	speaker 64 utterance 10????
	
	List of oov word types with occurences counts: 
		Counter(
			{u'yun3deng3': 1, 
			u'tong3yi1zhan4xian4zhan4xian4': 1, 
			u'xing4ju4liao3jie3': 1, 
			u'tong3yi1zhan4xian4ta1': 1}
		)
	Dictionary has a lot of entries...
"""


import tempfile
import codecs
import os
import logging

logger = logging.getLogger('Mandarin')


# all these files are empty in the original GlobalPhone Mandarin distribution
# there is also no transcription corresponding to these files
corrupted_wavs = [
	'CH046_34', 'CH046_35', 'CH046_36', 'CH046_37',
	'CH046_38', 'CH046_39', 'CH046_40', 'CH046_41',
	'CH046_42', 'CH046_43', 'CH046_44', 'CH046_45',
	'CH046_46', 'CH046_47', 'CH046_48', 'CH046_49',
	'CH046_50', 'CH046_51', 'CH046_52', 'CH046_53',
	'CH046_54', 'CH046_55', 'CH046_56', 'CH046_57',
	'CH046_58', 'CH046_59', 'CH046_60', 'CH046_61',
	'CH046_62', 'CH046_63', 'CH046_64', 'CH046_65',
	'CH046_66', 'CH046_67', 'CH046_68', 'CH046_69',
	'CH046_70', 'CH046_71', 'CH046_72', 'CH046_73',
	'CH046_74', 'CH046_75', 'CH046_76', 'CH046_77']


# there are wavefiles for these utterances, but no transcription
missing_transcripts = [
	'CH025_76', 'CH025_77', 'CH025_78', 'CH025_79', 
	'CH073_119', 'CH073_118', 'CH073_62', 'CH084_117', 
	'CH073_117', 'CH076_103', 'CH073_63', 'CH025_90', 
	'CH025_91', 'CH025_92', 'CH091_43', 'CH064_128', 
	'CH084_103', 'CH063_121', 'CH051_81', 'CH076_116', 
	'CH076_117', 'CH025_89', 'CH025_88', 'CH025_83', 
	'CH025_82', 'CH025_81', 'CH025_80', 'CH025_87', 
	'CH025_86', 'CH025_85', 'CH025_84']

exclude_wavs = corrupted_wavs + missing_transcripts



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


def correct(raw_transcript_folder, raw_dictionary_file):
	new_dictionary = correct_dictionary(raw_dictionary_file)
	new_transcript_folder = raw_transcript_folder  # nothing to do for the transcriptions
	return new_transcript_folder, new_dictionary