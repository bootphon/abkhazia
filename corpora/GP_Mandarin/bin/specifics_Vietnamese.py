# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 22:33:43 2015

@author: Thomas Schatz
"""

"""
Caveats:
	- clipping problems in certain wavefiles
	- for now we use a lexicon of monosyllables (see below)	
	correspond to linguistic structure, but not appropriate for ASR...
	- the dictionary is considerably smaller than that from Mandarin for some reason,
	even with the polysyllable artificial constructs

Transcript and lexicon problems:
	Multisyllabic units:
		starting from speaker 200 till last speaker 208 seem to not have been prepared like the rest
		of the transcriptions(supplementary speaker for phone variety?)
		Many double spacings in text and also same speakers have '_' linking some words.
		The '_' indicates multisyllabic compounds that actually are not really words but are useful for ASR.
		These compounds are in the dictionary, however they are not in the transcription for the main set
		of speakers (before speaker 200). 
			- We could try to parse the transcription with the dictionary, but there might be some
			ambiguities.
			- Before that, we should ask for the original from the authors or get confirmation 
			that they are not useful for training, only for recognition, in which case having them in
			the lexicon is enough, although it means that we will have to remove the '_' from the produced
			transcripts to measure the performance and we will only have performance on monosyllables
			(and we can actually check whether having kept the '_' in lexicon makes any difference)
			- For now, we just get rid of the transcription '_'. 
			Should we also remove those entries from the lexicon? W
				-> We should try both and checks that keeping them increase performance on monosyllables 
				(see discussion above)

	Other problems:	
		- There are transcriptions for alphabet letters that are very weird (e.g. letter K
		transcribed as k instead of ka or something else with a vowel), the secondary transcriptions
		often as 'j' for these letters also seem weird.
		- Also there seem to be homophonic transcription for uppercase and lowercase version of some
		word... Is that because one is a proper name? Otherwise we should get rid of it both in
		dictionary and text (some do occur in text such as À/à or A/a; see remarks on homophones below)
		- Proper names are not transcribed in the Dict although there is quite a lot of them in the
		text (see data_validation.py log for a complete list of OOV items)

	Homophones:
		Homophones will impair WER measures for no good reason, in particular
		when using a simple loop language model, so we might get rid of them,
		although this might cause problem when using the language models compiled
		for the original dictionary	(but we might have to change these because of 
		the changes we already introduced anyway)
 
		Example of homophones: loại/lọai, dao/giao, and many more... 
		Quite a few occuring in text and sometimes seem bad (lowercase and uppercase versions
		for example) 
		Note that transcribing proper names might add some more homophones
		On the other hand using multisyllabic word units might reduce the number of actual
		occurences of homophic pairs in the corpus
		(see data_validation.py log for a detailed account)
		
Alternative pronunciations:
	In the Vietnamese dictionary alternative pronunciations are supplied 
	for certain words, but they are not explicitly used in the text
	there are never more than two version of a given word
	
	For now we simply drop them
	
	Note that kaldi can accomodate alternative pronunciation and even
	pronunciation probabilities without problems, but using them in ABX 
	would be bothersome
	
	One possibility to accomodate several pronunciation would be to have an 
	optional lexicon_with_variants.txt file, optionally also with probabilities
	that would be used by kaldi
	Then one could either ignore the variants in ABX or use the kaldi acoustic models
	to do a hard assignment of each occurence of each word to a given pronunciation
	
	Here we make the assumption that the first pronunciation (without the (2) suffix)
	is the more likely
	We could check this assumption by comparing WERs with first or second variant or both
"""


import tempfile
import codecs
import os
import re
import logging


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
		# skip secondary pronunciations
		if not(u"(2)" in line):
			# skip some words
			if all([not(u"{"+word+u"}" in line) for word in words_to_drop]):
				# rewrite tone markers in a manner consistent
				# with GlobalPhone Mandarin pinyin markings
				if u"WB " in line:
					line = line.replace(u"WB ", u"WB")
				if u"  " in line:
					line = line.replace(u"  ", u" ")
				if u"{{t}" in line:  # ttd and t.t.d have wrongly formatted transcriptions
					line = line.replace(u"{{t}", u"{t")
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


# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']


def correct_transcripts(transcript_folder):
	"""
	script to correct problems with the original Global Phone Vietnamese transcripts
	the corrections are completely ad hoc:
		- remove trailings spaces and all double spacings and '_' from transcriptions
		on every odd line but the first	
		(double spacings and '_' are actually only found for speakers 200 to 208)
	the result are stored in a temporary folder
	"""
	logger.info("Correcting transcripts")	
	files = list_dir(transcript_folder)
	# generate temporary output folder
	output_folder = tempfile.mkdtemp()
	for f in files:
		# read transcript file
		filename = os.path.join(transcript_folder, f)
		with codecs.open(filename, mode='r', encoding='UTF-8') as inp:
			lines = inp.readlines()
		# correct odd lines
		lines[2::2] = [line.replace(u"_", u" ").replace(u"  ", u" ").strip() + u"\n" for line in lines[2::2]]
		# write corrected version to temp
		output_file = os.path.join(output_folder, f)
		with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
			for line in lines:
				out.write(line)
	logger.info("Transcripts corrected")
	return output_folder
	
	
def correct(raw_transcript_folder, raw_dictionary_file):
	new_dictionary = correct_dictionary(raw_dictionary_file)
	new_transcript_folder = correct_transcripts(raw_transcript_folder)
	return new_transcript_folder, new_dictionary