# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 22:33:43 2015

@author: Thomas Schatz
"""

"""
	Caveats:
		- Speakers have regional accents: this limits the detail into which one can go
		for phonological or linguistic analysis based on this corpus
		- Dictionary has a lot of entries... supposed to be constructed
		from text, so why much of it is not used? Maybe it was built with
		the larger corpus of text used for Language Model generation? 
		We need to ask this to the corpus builders.
		- Word units do not correspond to actual words, whatever this might means
		in Mandarin (e.g. 'notsure' could be a word in English with this approach)
	
	Mismatched audio and transcripts:
		speaker 84 seems all mixed up, list of main defects found:
			audio 100 -> transcription 102	
			audio 102 -> transcription 10
			audio 104 -> transcription 108
			audio 105 -> transcription 107
			audio 107 -> transcription 100
			audio 108 -> transcription 105
			audio 109 -> transcription 104
			audio 110 -> transcription 11
			audio 111 -> transcription 116
			audio 112 -> transcription 115
			audio 113 -> transcription 114
			audio 114 -> transcription 110
			audio 115 -> transcription 113
			audio 116 -> transcription 112
			audio 10 -> no corresponding transcript?
			audio 11 -> no corresponding transcript?
			there are also two audio files (103 and 117) with no associated transcript
			maybe one correspond to transcription 111, which does not seem to be associated
			to any other audio	
		speaker 63 utterance 10????
		speaker 64 utterance 10????
		And probably many more...

	OOV: 
		They are not really OOV, only some transcript contain the correct sentence plus
		a part of it that has been duplicated for some reason. In general, the duplicated
		part is pasted first, then the correct full sentence is concatenated to it without
		point or spaces, yielding the OOV items as a concatenation of the last word of the
		fragment and the first word of the sentence.
		There is only one OOV item not conforming to this pattern: tong3yi1zhan4xian4zhan4xian4,
		where the actual word is 'tong3yi1zhan4xian4' but the speaker hesitated between yi1 and
		zhan4xian4. For this utterance, see what has been done for other sentences with hesitations
		and do the same (either ignore it and transcribe as tong3yi1zhan4xian4 or throw away the
		utterance?).
		
		List of oov word types with occurences counts: 
		Counter(
			{u'yun3deng3': 1, 
				need to remove begginning + this one has in addition a bad transcription 
				'hai2you3 hai2you3 hai2you3 yu2 dui4 yun3 yun3' which does not match
				the audio file
			u'tong3yi1zhan4xian4zhan4xian4': 1,
				need to remove begginning 
			u'xing4ju4liao3jie3': 1,
				need to remove beginning (ju4liao3jie3 wei2 jia1qiang2 liang2 you2 shi4chang3 de5
				hong2guan1 diao4 kong4 guo2wu4yuan4 qu4nian2 jue2ding4 liang2shi5 qi3ye4 de5 
				zheng4ce4 xing4)
			u'tong3yi1zhan4xian4ta1': 1} 
				not the same problem (see above) but in the same sentence as another OOV
		)
		
	TODO:
		Detect potential defective transcripts:
			1. look for very unlikely sentences with kaldi
			and see whether this way we can reliably detect the oov utterances and the utterances with known
			transcription problems
			2. look for transcriptions which contain a long substring that is repeated 
			(find longest repeating substring or longest matching substring with edit distance
			lower than xxx) (removing all spaces from the transcription) and check that we find
			the oov sentences this way
			(3. have somebody read the transcript and simultaneously listen to the audio and note
			every mismatch)
		Then have somebody check and correct the problematic transcripts
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
	new_transcript_folder = raw_transcript_folder  # we do nothing to for the transcriptions for now
	return new_transcript_folder, new_dictionary