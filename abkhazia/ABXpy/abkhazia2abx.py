# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 15:05:38 2014

@author: Thomas Schatz
"""

import codecs
from itertools import groupby


def alignment2item(alignment_file, item_file, spk_id_len, segment_extension='single_phone'):
	"""
	Creates an item file suitable for most standard ABX tasks on speech corpora.
	Input is an abkhazia formatted alignment file for a given corpus.
	Output is a .item file suitable for use with ABXpy.

	Features for use with this item file should be in h5features format with one internal file by
	utterance (using the utterance-id as filename) and times given relative to the beginning of
	the utterance.

	segment_extension: string, can be 'single_phone' (each item correspond to a
		portion of signal corresponding to a single phone), 'triphone' (each
		item correspond to a portion of signal corresponding to three consecutive
		phones), 'half_triphone' (each item correspond to a portion of signal
		corresponding to a phone with half the preceding and half the following
		phones). Note that none of these affects the content of the 'context' column
		in the output file, only the timestamps differ.
	"""
	assert segment_extension in ['single_phone', 'triphone', 'half_triphone']
	# read alignment file
	with codecs.open(alignment_file, mode='r', encoding='UTF-8') as inp:
		all_lines = inp.readlines()
	# open item_file and write to it
	with codecs.open(item_file, mode='w', encoding='UTF-8') as out:
		# write header
		out.write('#file onset offset #phone prev_phone next_phone talker\n')
		# gather and process each utterance independently
		get_utt_id = lambda line: line.split()[0]
		for utt_id, lines in groupby(all_lines, get_utt_id):  # group by utt_id
			lines = list(lines)  # convert itertools object into list
			speaker = utt_id[:spk_id_len]
			# use the first phone only in 'single_phone' case
			if segment_extension == 'single_phone':
				_, start, stop, phone = lines[0].split()
				if len(lines) == 1:
					next = 'SIL'
				else:
					next = lines[1].split()[3]
				info = [utt_id, start, stop, phone, 'SIL', next, speaker]
				out.write(u" ".join(info) + u"\n")
			# middle lines
			for prev_l, line, next_l in zip(lines[:-2], lines[1:-1], lines[2:]):
				_, prev_start, prev_stop, prev_phone = prev_l.split()
				_, start, stop, phone = line.split()
				_, next_start, next_stop, next_phone = next_l.split()
				if segment_extension == 'triphone':
					seg_start, seg_stop = prev_start, next_stop
				elif segment_extension == 'half_triphone':
					seg_start, seg_stop = (prev_start+start)/2., (stop + next_stop)/2.
				else:
					seg_start, seg_stop = start, stop
				info = [utt_id, seg_start, seg_stop, phone, prev_phone, next_phone, speaker]
				out.write(u" ".join(info) + u"\n")
			# use the last line only in 'single_phone' case
			if segment_extension == 'single_phone':
				if len(lines) > 1:  # do not process twice the same line as first and last line!
					_, start, stop, phone = lines[-1].split()
					prev = lines[-2].split()[3]
					info = [utt_id, start, stop, phone, prev, 'SIL', speaker]
					out.write(u" ".join(info) + u"\n")

# test 
alignment_file = '/Users/thomas/Documents/PhD/Recherche/test/forced_alignment.txt'
item_file = '/Users/thomas/Documents/PhD/Recherche/test/WSJ.item'
spk_id_len = 3
alignment2item(alignment_file, item_file, spk_id_len, 'triphone')
	

