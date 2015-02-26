# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation GlobalPhone Mandarin and Vietnamese

wav extraction requires shorten and sox on the path.
"""

import os
import subprocess as sp
import codecs
import re
import importlib
import logging

# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']
	

def extract_wav(input_dir, output_dir):
	"""
	input_dir is the 'adc' directory from the GlobalPhone distribution of the 
	language considered
	"""
	fs = 16000  # sampling frequency of the input files in Hz
	nbits = 16  # each sample is coded on 16 bit in the input files
	
	if not(os.path.isdir(output_dir)):
		os.mkdir(output_dir)
	l = list_dir(input_dir) 
	for e in l:
		d = os.path.join(input_dir, e)
		spns = list_dir(d)
		for spn in spns:
			raw = spn.replace('.adc.shn', '.raw')
			wav = raw.replace('.raw', '.wav')
			spn_file = os.path.join(d, spn)
			raw_file = os.path.join(output_dir, raw)
			wav_file = os.path.join(output_dir, wav)
			sp.call("shorten -x {0} {1}".format(spn_file, raw_file), shell=True)
			sp.call("sox -t raw  -r {0} -e signed-integer -b {1} {2} -t wav {3}".format(
				fs, nbits, raw_file, wav_file), shell=True)
			os.remove(raw_file)


def utt_list(wav_dir, output_file):
	files = list_dir(wav_dir)	
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for f in files:
			utt_id = f.replace('.wav', '')
			out.write(u"{0} {1}\n".format(utt_id, f))


def spk_list(wav_dir, output_file):
	files = list_dir(wav_dir)	
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for f in files:
			utt_id = f.replace('.wav', '')
			spk_id = f[:5]
			out.write(u"{0} {1}\n".format(utt_id, spk_id))


def extract_transcript(input_dir, output_file):
	files = list_dir(input_dir)
	all_transcripts = []
	all_ids = []
	for f in files:
		spk_id = os.path.splitext(f)[0]
		filename = os.path.join(input_dir, f)
		with codecs.open(filename, mode='r', encoding='UTF-8') as inp:
			l = inp.readlines()
			# get every even line starting from line 2
			even_lines = l[1::2]
			# remove :, ; and space and tabs
			ids = [re.sub(u"\s+|:|;", u"", e) for e in even_lines]
			all_ids = all_ids + [spk_id + u"_" + e for e in ids]
			# get every odd line starting from line 3
			odd_lines = l[2::2]
			# standardize linebreaks
			# this does not take into account fancy unicode linebreaks
			# see: http://stackoverflow.com/questions/3219014/what-is-a-cross-platform-regex-for-removal-of-line-breaks
			transcripts = [re.sub(u"\r\n?|\n", u"\n", e) for e in odd_lines]
			all_transcripts = all_transcripts + transcripts
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for i, t in zip(all_ids, all_transcripts):
			out.write(u"{0} {1}".format(i, t))


def export_phones(phones, output_folder, silences=None, variants=None):
	output_file = os.path.join(output_folder, 'phones.txt')	
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for phone in phones:
			out.write(u"{0} {1}\n".format(phone, phones[phone]))
	if not(silences is None):
		output_file = os.path.join(output_folder, 'silences.txt')
		with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
			for sil in silences:
				out.write(sil + u"\n")
	if not(variants is None):
		output_file = os.path.join(output_folder, 'extra_questions.txt')
		with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
			for l in variants:
				out.write(u" ".join(l) + u"\n")


def strip_accolades(s):
	assert s[0] == "{" and s[-1] == "}", u"Bad formatting for word or transcript: {0}".format(s)
	return s[1:-1]


def extract_dictionary(dictionary_file, output_file, words_to_drop=None):
	# read input file
	with codecs.open(dictionary_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	# get rid of linebreaks
	# this does not take into account fancy unicode linebreaks
	# see: http://stackoverflow.com/questions/3219014/what-is-a-cross-platform-regex-for-removal-of-line-breaks
	lines = [re.sub(u"\r\n?|\n", u"", line) for line in lines]
	# parse input file
	words = []
	transcripts = []
	for line in lines:
		l = line.split(u" ")
		word = l[0]
		transcript = l[1:]
		# parse word
		word = strip_accolades(word)
		assert not u"{" in word
		# parse phonetic transcription
		t = u" ".join(transcript)
		t = strip_accolades(t)
		t = t.split(u" ")
		transcript = []
		for phone in t:
			assert phone, t  # check that transcription is not empty
			if phone[0] == u"{":
				p = phone[1:]
				assert p != u"WB", t
			elif phone[-1] == u"}":
				p = phone[:-1]
				assert p == u"WB", t
			else:
				p = phone
				assert p != u"WB", t
			assert not(u"{" in p), t
			if p != u"WB":
				transcript.append(p)
		transcript = u" ".join(transcript)
		words.append(word)
		transcripts.append(transcript)
	# generate output file
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for w, t in zip(words, transcripts):
			out.write(u"{0} {1}\n".format(w, t))


# languages to be prepared
languages = ['Mandarin', 'Vietnamese']
# name of the folder in the raw distribution containing the transcriptions to be used
transcript = {'Mandarin': 'rmn', 'Vietnamese': 'trl'}

# path to a directory containing the raw ELRA distribution for the desired languages
# it should contain folders named GlobalPhone-"name of language", for example
# GlobalPhone-Mandarin or GlobalPhone-Vietnamese
raw_path = "/Users/thomas/Documents/PhD/Recherche/Code/BuckeyeChallenge/GLOBALPHONE"
# path to a directory containing the raw ELRA distribution for the phonetic dictionaries
# for the desired languages
# it should contain folders named GlobalPhoneDict-"name of language", for example
# GlobalPhoneDict-Mandarin or GlobalPhoneDict-Vietnamese
raw_dict_path = "/Users/thomas/Documents/PhD/Recherche/Code/BuckeyeChallenge/GLOBALPHONE"
# path to a directory where the processed corpora is to be stored
processed_path = "/Users/thomas/Documents/PhD/Recherche/databases/abkhazia/corpora"

# log files config
loggers = {}
for lang in languages:
	loggers[lang] = logging.getLogger(lang)
	loggers[lang].setLevel(logging.DEBUG)
	log_file = os.path.join(processed_path, "GP_{0}/logs/data_preparation.log".format(lang))
	log_handler = logging.FileHandler(log_file, mode='w')
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	log_handler.setFormatter(formatter)
	log_handler.setLevel(logging.DEBUG)
	loggers[lang].addHandler(log_handler)


##########################
## I. Speech recordings ##
##########################
"""
for lang in languages:
	loggers[lang].info("Copying wav files")
	i = os.path.join(raw_path, "GlobalPhone-{0}/{0}/adc".format(lang))
	o = os.path.join(processed_path, "GP_{0}/data/wavs".format(lang))
	extract_wav(i, o)
	loggers[lang].info("Wav files copied")
"""
# Note: Ask database creator about clipping problems in Vietnamese?

############################
## II. List of utterances ##
############################
"""
for lang in languages:
	loggers[lang].info("Generating utterances list")
	wav_dir = os.path.join(processed_path, "GP_{0}/data/wavs".format(lang))
	utt_file = os.path.join(processed_path, "GP_{0}/data/segments".format(lang))
	utt_list(wav_dir, utt_file)
	loggers[lang].info("Utterances list generated")
"""

###########################
## III. List of speakers ##
###########################
# Note: more info on speakers is available in spk folders of the raw distributions
"""
for lang in languages:
	loggers[lang].info("Generating speakers list")
	wav_dir = os.path.join(processed_path, "GP_{0}/data/wavs".format(lang))
	spk_file = os.path.join(processed_path, "GP_{0}/data/utt2spk".format(lang))
	spk_list(wav_dir, spk_file)
	loggers[lang].info("Speaker list generated")
"""

#######################
## IV. Transcription ##
#######################	
"""
for lang in languages:
	loggers[lang].info("Generating utterances transcriptions")
	transcript_dir = os.path.join(raw_path, "GlobalPhone-{0}/{0}/{1}".format(lang, transcript[lang]))
	text_file = os.path.join(processed_path, "GP_{0}/data/text".format(lang))
	extract_transcript(transcript_dir, text_file)
	loggers[lang].info("Utterances transcription generated")
"""

########################
## V. Phone inventory ##
########################

for lang in languages:
	loggers[lang].info("Creating phone inventory")
	phoneset = importlib.import_module('phoneset_{0}'.format(lang))
	output_folder = os.path.join(processed_path, "GP_{0}/data".format(lang))
	export_phones(phoneset.phones, output_folder, phoneset.silences, phoneset.variants)
	loggers[lang].info("Phone inventory created")

#############################
## VI. Phonetic dictionary ##
#############################

for lang in languages:
	loggers[lang].info("Generating phonetic dictionary")
	dictionary_file = os.path.join(raw_dict_path, "GlobalPhoneDict-{0}/{0}-GPDICT.txt".format(lang))
	output_file = os.path.join(processed_path, "GP_{0}/data/lexicon.txt".format(lang))
	# some dictionaries are distributed with formating errors or unused words
	# we use a language-specific script to correct them
	# the result is put in a temporary file
	dict_module = importlib.import_module('dictionary_{0}'.format(lang))
	corrected_dict_file = dict_module.correct_dictionary(dictionary_file)
	# then we use a generic script to put dictionaries in abkhazia format
	extract_dictionary(corrected_dict_file, output_file)
	# remove temporary dict file
	os.remove(corrected_dict_file)
	loggers[lang].info("Phonetic dictionary generated")
# Note: evaluate potential benefits of using the ignored secondary pronunciation in Vietnamese?
