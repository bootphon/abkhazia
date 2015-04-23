# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Functions for reading and sorting the various Abkhazia file formats.
"""

import os
import subprocess
import codecs
import wave
import numpy as np


def cpp_sort(filename):
	# there is redundancy here but I didn't check which export can be 
	# safely removed, so better safe than sorry
	os.environ["LC_ALL"] = "C"
	subprocess.call("export LC_ALL=C; sort {0} -o {1}".format(filename, filename), shell=True, env=os.environ)


def basic_parse(line, filename):
	# check line break
	assert not('\r' in line), "'{0}' contains non Unix-style linebreaks".format(filename)
	# check spacing
	assert not('  ' in line), "'{0}' contains lines with two consecutive spaces".format(filename)
	# remove line break
	line = line[:-1]
	# parse line
	l = line.split(" ")
	return l


def read_utt2spk(filename):
	utt_ids, speakers = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2), "'utt2spk.txt' should contain only lines with two columns"
		utt_ids.append(l[0])
		speakers.append(l[1])
	return utt_ids, speakers


def read_segments(filename):
	utt_ids, wavs, starts, stops = [], [], [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2 or len(l) == 4), \
			"'segments.txt' should contain only lines with two or four columns"
		utt_ids.append(l[0])
		wavs.append(l[1])
		if len(l) == 4:
			starts.append(float(l[2]))
			stops.append(float(l[3]))
		else:
			starts.append(None)
			stops.append(None)
	return utt_ids, wavs, starts, stops


def read_text(filename):
	utt_ids, utt_words = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) >= 2), "'text.txt' should contain only lines with two or more columns"
		utt_ids.append(l[0])
		utt_words.append(l[1:])
		if u"" in l[1:]:
			print line
	return utt_ids, utt_words


def read_phones(filename):
	phones, ipas = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2), "'phones.txt' should contain only lines with two columns"
		phones.append(l[0])
		ipas.append(l[1])
	return phones, ipas


def read_silences(filename):
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
		assert(len(l) >= 2), \
			"'variants.txt' should contain only lines with two or more columns"
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


def get_utt_durations(wav_dir, seg_file):
	# get wavefiles durations
	wavefiles = [e for e in os.listdir(wav_dir) if e != .DS_store]
	wav_durations = {}
	for f in wavefiles:
		filepath = os.path.join(wav_dir, f)
		with contextlib.closing(wave.open(filepath,'r')) as fh:
			_, _, rate[f], nframes[f], _, _ = fh.getparams()
	    	wav_durations[f] = nframes[f]/float(rate[f])
	# get utterance durations
	utt_ids, wavs, starts, stops = read_segments(seg_file)
	utt_durations = {}
	for utt_id, wav, start, stop in zip(utt_ids, wavs, starts, stops):
		start = 0 if start is None else start
		stop = wav_durations[wav] if stop is None else stop
		utt_durations[utt_id] = stop-start
	return utt_durations


def match_on_first_col(lines, desired_first_col):
	first_col = [line.strip().split(u" ")[0] for line in lines]
	# need numpy here to get something fast easily
	# could also have something faster with pandas
	# see http://stackoverflow.com/questions/15939748/check-if-each-element-in-a-numpy-array-is-in-another-array
	indices = np.where(np.in1d(np.array(first_col), np.array(desired_first_col)))[0]
	lines = list(np.array(lines)[indices])		
	return lines


def copy_match(file_in, file_out, get_matches):
      """
      Utility function to copy only certain lines of a file
      as decided by the get_matches function provided as argument
      """
      with codecs.open(file_in, mode='r', encoding='UTF-8') as inp:
    		lines = inp.readlines()
      lines = get_matches(lines)
      with codecs.open(file_out, mode='w', encoding='UTF-8') as out:
    		for line in lines:
    			out.write(line)


def copy_first_col_matches(file_in, file_out, desired_first_col):
	get_matches = lambda lines: match_on_first_col(lines, desired_first_col)
	copy_match(file_in, file_out, get_matches)
