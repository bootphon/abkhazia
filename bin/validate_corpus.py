# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
This script checks whether a given speech corpus is correctly formatted 
for usage with abkhazia tools
"""

#TODO: add stream handler with only severe problems reporting
#TODO: report log summary on stream handler (number of warnings etc.)
#TODO: get rid of empty wav files


import contextlib
import logging
import os
import wave
import codecs
import subprocess


def cpp_sort(filename):
	# there is redundancy here but I didn't check which export can be 
	# safely removed, so better safe than sorry
	os.environ["LC_ALL"] = "C"
	subprocess.call("export LC_ALL=C; sort {0} -o {1}".format(filename, filename), shell=True, env=os.environ)


#TODO: share these functions between modules

def basic_parse(line, filename):
	# check line break
	assert not('\r' in line), "'{0}' contains non Unix-style linebreaks".format(filename)
	# check spacing
	assert not('  ' in line), "'{0}' contains line with double spacings".format(filename)
	# remove line break
	line = line[:-1]
	# parse line
	l = line.split(" ")
	return l


def read_segments(filename):
	utt_ids, wavs, starts, stops = [], [], [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2 or len(l) == 4), "'segments' should contain only lines with two or four columns"
		utt_ids.append(l[0])
		wavs.append(l[1])
		if len(l) == 4:
			starts.append(float(l[3]))
			stops.append(float(l[4]))
		else:
			starts.append(None)
			stops.append(None)
	return utt_ids, wavs, starts, stops


def read_utt2spk(filename):
	utt_ids, speakers = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2), "'utt2spk' should contain only lines with two columns"
		utt_ids.append(l[0])
		speakers.append(l[1])
	return utt_ids, speakers


def read_text(filename):
	utt_ids, utt_words = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) >= 2), "'utt2spk' should contain only lines with two or more columns"
		utt_ids.append(l[0])
		utt_words.append(l[1:])
	return utt_ids, utt_words


def	read_phones(filename):
	phones, ipas = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2), "'phones.txt' should contain only lines with two columns"
		phones.append(l[0])
		ipas.append(l[1])
	return phones, ipas


def	read_silences(filename):
	silences = []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 1), "'silences.txt' should contain only lines with one column"
		silences.append(l[0])
	return silences


def read_variants(filename):
	variants = []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) >= 2), "'extra_questions.txt' should contain only lines with two or more columns"
		variants.append(l)
	return variants


def read_dictionary(filename):
	dict_words, transcriptions = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) >= 2), "'lexicon.txt' should contain only lines with two or more columns"
		dict_words.append(l[0])
		transcriptions.append(l[1:])
	return dict_words, transcriptions


def validate(corpus_path):

	"""
	Check corpus directory structure
	"""
	data_dir = os.path.join(corpus_path, 'data')
	if not(os.path.isdir(data_dir)):
		raise IOError("Corpus folder {0} should contain a 'data' subfolder".format(corpus_path))
	log_dir = os.path.join(corpus_path, 'logs')
	if not(os.path.isdir(log_dir)):
		raise IOError("Corpus folder {0} should contain a 'logs' subfolder".format(corpus_path))	
	
	# log file config
	log = logging.getLogger()
	log.setLevel(logging.DEBUG)
	log_file = os.path.join(log_dir, "data_validation.log".format(corpus_path))
	log_handler = logging.FileHandler(log_file, mode='w')
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	log_handler.setFormatter(formatter)
	log_handler.setLevel(logging.DEBUG)
	log.addHandler(log_handler)


	"""
	wav directory must contain only mono wavefiles in 16KHz, 16 bit PCM format
	"""
	log.info("Checking 'wavs' folder")
	wav_dir = os.path.join(data_dir, 'wavs')
	wavefiles = os.listdir(wav_dir)
	durations = {}
	l = [f[-4:] == ".wav" for f in wavefiles]
	if not(all(l)):
		f = wavefiles[l.index[False]]
		raise IOError("file {0} in 'wavs' folder doesn't have a '.wav' extension".format(f))
	for f in wavefiles:
		filepath = os.path.join(wav_dir, f)
		with contextlib.closing(wave.open(filepath,'r')) as fh:
			(nb_channels, width, rate, nframes, comptype, compname) = fh.getparams()
	    	if nframes == 0:
	    		log.warning('file {0} is empty'.format(f))
	    	if rate != 16000:
	    		raise IOError('currently only files sampled at 16,000 Hz are supported. \
	    						File {0} is sampled at {1} Hz'.format(f, rate))
	    	if nb_channels != 1:
	    		raise IOError('file {0} has {1} channels, only files with 1 channel \
	    						are currently supported'.format(f, nb_channels))
	    	if width != 2:  # in bytes: 16 bit == 2 bytes
	    		raise IOError('file {0} is encoded on {1} bits, only files encoded \
	    						on 16 bits are currently supported'.format(f, 8*width))
	    	if comptype != 'NONE':
	    		raise IOError('file {0} is compressed'.format(f))
	    	durations[f] = nframes/float(rate)
	log.info("'wavs' folder is OK")


	"""
	checking utterances list
	"""
	log.info("Checking 'segments' file")
	log.info("C++ sort file")
	seg_file = os.path.join(data_dir, "segments")
	cpp_sort(seg_file)  # C++ sort file for convenience
	utt_ids, wavs, starts, stops = read_segments(seg_file)
	# unique utterance-ids
	assert len(utt_ids) == len(set(utt_ids)), "utterance-ids in 'segments' are not unique"
	# all referenced wavs are in wav folder
	for wav in wavs:
		assert wav in wavefiles, "file {0} referenced in 'segments' is not in wav folder".format(wav)
	# start and stop are consistent and compatible with file duration
	for start, stop, wav, utt_id in zip(starts, stops, wavs, utt_ids):
		if not(start is None):
			assert stop >= start, "Stop time for utterance {0} is lower than start time".format(utt_id)  # should it be >?
			duration = durations[wav]
			assert 0 <= start <= duration, "Start time for utterance {0} is not compatible with file duration".format(utt_id)
			assert 0 <= stop <= duration, "Stop time for utterance {0} is not compatible with file duration".format(utt_id)
	#TODO: log warnings if there is overlap in time between different utterances
	log.info("'segments' file is OK")

	
	"""
	checking speakers list
	"""
	log.info("Checking 'speakers' file")
	log.info("C++ sort file")
	spk_file = os.path.join(data_dir, "utt2spk")
	cpp_sort(spk_file)  # C++ sort file for convenience
	utt_ids_spk, speakers = read_utt2spk(spk_file)
	# same utterance-ids
	assert(utt_ids_spk == utt_ids), "Utterance ids in 'segments' and 'utt2spk' are not consistent"
	# speaker ids must have a fixed length
	l = len(speakers[0])
	assert all([len(s) == l for s in speakers]), "All speaker-ids must have the same length"
	# each speaker id must be prefix of corresponding utterance-id
	for utt, spk in zip(utt_ids, speakers):
		assert utt[:l] == spk, "All utterance-ids must be prefixed by the corresponding speaker-id"
	log.info("'speakers' file is OK")
	

	"""
	checking transcriptions
	"""
	log.info("Checking 'text' file")
	log.info("C++ sort file")
	txt_file = os.path.join(data_dir, "text")
	cpp_sort(txt_file)  # C++ sort file for convenience
	utt_ids_txt, utt_words = read_text(txt_file)
	# we will check that the words are mostly in the lexicon later
	# same utterance-ids
	assert(utt_ids_txt == utt_ids), "Utterance ids in 'segments' and 'text' are not consistent"
	# TODO log missing wavs and missing transcriptions	
	log.info("'text' file is OK, checking for OOV items later")


	"""
	checking phone inventory
	"""
	# phones
	#TODO: check xsampa compatibility and/or compatibility with articulatory features databases of IPA
	# or just basic IPA correctness
	phon_file = os.path.join(data_dir, "phones.txt")
	phones, ipas = read_phones(phon_file)
	assert not(u"SIL" in phones)
	assert not(u"SPN" in phones)
	assert len(phones) == len(set(phones))
	assert len(ipas) == len(set(ipas))
	# silences
	sil_file = os.path.join(data_dir, "silences.txt")
	if not(os.path.exists(sil_file)):
		log.info("No silences.txt file, creating default one")
		with codecs.open(sil_file, mode='w', encoding="UTF-8") as out:
			out.write(u"SIL\n")
			out.write(u"SPN\n")
	else:
		sils = read_silences(sil_file)
		assert len(sils) == len(set(sils))
		if not u"SIL" in sils:
			log.info("Adding missing 'SIL' symbol to silences.txt")
			with codecs.open(sil_file, mode='a', encoding="UTF-8") as out:
				out.write(u"SIL\n")
			sils.append(u"SIL")
		if not u"SPN" in sils:
			log.info("Adding missing 'SPN' symbol to silences.txt")
			with codecs.open(sil_file, mode='a', encoding="UTF-8") as out:
				out.write(u"SPN\n")
			sils.append(u"SPN")
		assert not(set.intersection(set(sils), set(phones)))
	# variants
	var_file = os.path.join(data_dir, "extra_questions.txt")
	if not(os.path.exists(var_file)):
		log.info("No extra_questions.txt file, creating empty one")
		with codecs.open(var_file, mode='w', encoding="UTF-8") as out:
			pass
	else:	
		variants = read_variants(var_file)
		all_symbols = [symbol for group in variants for symbol in group]
		for symbol in all_symbols:
			assert symbol in phones or symbol in sils, symbol
		assert len(all_symbols) == len(set(all_symbols))
	inventory = set.union(set(phones), set(sils))

	"""
	checking phonetic dictionary
	"""
	dict_file = os.path.join(data_dir, "lexicon.txt")
	dict_words, transcriptions = read_dictionary(dict_file)
	# unique word entries (for now we don't accept alternative pronunciations)
	assert len(dict_words) == len(set(dict_words))
	# OOV item
	if not(u"<UNK>" in dict_words):
		log.info("No '<UNK>' word in lexicon, adding one")
		with codecs.open(sil_file, mode='a', encoding="UTF-8") as out:
				out.write(u"<UNK> SPN\n")
		dict_words.append(u"<UNK>")
		transcriptions.append([u"SPN"])
	else:
		unk_transcript = transcriptions[dict_words.index(u"<UNK>")]
		assert unk_transcript == [u"SPN"]
	#TODO log a warning for all words containing silence phones?
	# unused words
	used_words = [word for words in utt_words for word in words]
	used_words_unique = set(used_words)
	unused_words = [word for word in dict_words if not(word in used_words_unique)]
	log.info("{0} unused words in phonetic dictionary".format(len(unused_words)))
	# oov words
	oov_words = [word for words in used_words if not(word in dict_words)]
	log.info("{0} oov word occurences in transcriptions".format(len(oov_words)))
	log.info("{0} oov word types in transcriptions".format(len(set(oov_words))))
	# ooi phones
	used_phones = [phone for trans_phones in transcriptions for phone in trans_phones]
	ooi_phones = [phone for phone in set(used_phones) if not(phone in inventory)]
	if ooi_phones:
		raise IOError("Phonetic dictionary uses out-of-inventory phones: {0}".format(ooi_phones))
	#TODO raise alarm if too large a proportion of oov words
	#TODO warning for unused phones? Or let that for statistics?


validate('/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/GP_Mandarin')