# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz


Getting forced alignments and posterior decoding on some corpora
"""

import codecs
import os

# phone file: phones.txt in lang_dir, tra_file: in export
def export_phone_alignment(phones_file, tra_file, out_file, word_position_dependent=True):
	with codecs.open(phones_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	int2phone = {}
	for line in lines:
		phone, code = line.strip().split(u" ")
		# remove word position markers
		if word_position_dependent:
			if phone[-2:] in ["_I", "_B", "_E", "_S"]:
				phone = phone[:-2]
		int2phone[code] = phone
	with codecs.open(tra_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	with codecs.open(out_file, mode='w', encoding='UTF-8') as out:
		for line in lines:
			sequence = line.strip().split(u" ; ")
			utt_id, code, nframes = sequence[0].split(u" ")
			sequence = [u" ".join([code, nframes])] + sequence[1:]
			start = 0.0125  # this seems good enough, but I didn't check in the make_mfcc code of kaldi to be sure
			for e in sequence:
				code, nframes = e.split(u" ")
				stop = start + 0.01*int(nframes)
				out.write(u"{0} {1} {2} {3}\n".format(utt_id, start, stop, int2phone[code]))
				start = stop

#TODO check alignment: which utt have been transcribed, have silence been inserted, otherwise
# no difference ? chronological order, grouping by utt_id etc.

root = "/Users/Thomas/Documents/PhD/Recherche/test"
phones_file = os.path.join(root, 'phones.txt')
tra_file = os.path.join(root, 'forced_alignment.tra')
out_file = os.path.join(root, 'forced_alignment.txt')
export_phone_alignment(phones_file, tra_file, out_file)

