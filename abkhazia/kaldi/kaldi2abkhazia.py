# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz


Exporting forced alignments from a kaldi recipe to abkhazia alignment format. 
"""

import codecs
import os


def read_kaldi_phonemap(phones_file, word_position_dependent=True):
	with codecs.open(phones_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	phonemap = {}
	for line in lines:
		phone, code = line.strip().split(u" ")
		# remove word position markers
		if word_position_dependent:
			if phone[-2:] in ["_I", "_B", "_E", "_S"]:
				phone = phone[:-2]
		phonemap[code] = phone
	return phonemap


def read_kaldi_alignment(phonemap,  tra_file):
	# tra_file using the format on each line: utt_id [phone_code n_frames]+
	# this is a generator (it yields in the loop)
	with codecs.open(tra_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	for line in lines:
		sequence = line.strip().split(u" ; ")
		utt_id, code, nframes = sequence[0].split(u" ")
		sequence = [u" ".join([code, nframes])] + sequence[1:]
		start = 0.0125  # this seems good enough, but I didn't check in the make_mfcc code of kaldi to be sure
		for e in sequence:
			code, nframes = e.split(u" ")
			stop = start + 0.01*int(nframes)
			yield utt_id, start, stop, phonemap[code]
			start = stop


def export_phone_alignment(phones_file, tra_file, out_file, word_position_dependent=True):
	# phone file: phones.txt in lang_dir, tra_file: in export
	phonemap = read_kaldi_phonemap(phones_file, word_position_dependent)
	with codecs.open(out_file, mode='w', encoding='UTF-8') as out:
		for utt_id, start, stop, phone in read_kaldi_alignment(phonemap, tra_file):
			out.write(u"{0} {1} {2} {3}\n".format(utt_id, start, stop, phone))


#TODO check alignment: which utt have been transcribed, have silence been inserted, otherwise
# no difference? (maybe some did not reach final state), chronological order, grouping by utt_id etc.


#root = "/Users/Thomas/Documents/PhD/Recherche/test"
#phones_file = os.path.join(root, 'phones_WSJ.txt')
#tra_file = os.path.join(root, 'WSJ_forced_alignment.tra')
#out_file = os.path.join(root, 'WSJ_forced_alignment.txt')
#export_phone_alignment(phones_file, tra_file, out_file)

