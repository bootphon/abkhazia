# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

import abkhazia.utilities.basic_io as io
import codecs
import os.path as p

def convert_text(lexicon, text_file, out_file):
	"""
	Create 'phone' version of text file (transcription of text directly into phones, without
	any word boundary marker). This is used to estimate phone-level n-gram language models
	for use with kaldi recipes.
	For OOVs: just drop the whole sentence for now.
	"""
	# set up dict
	words, transcriptions = io.read_dictionary(lexicon)
	dictionary = {}
	for word, transcript in zip(words, transcriptions):
		dictionary[word] = transcript
	# transcribe
	utt_ids, utt_words = io.read_text(text_file)
	with codecs.open(out_file, mode='w', encoding='UTF-8') as out:
		for utt_id, utt in zip(utt_ids, utt_words):
			try:
				hierarchical_transcript = [dictionary[word] for word in utt]
			except KeyError:
				continue  # OOV: for now we just drop the sentence silently in this case (could add a warning)
			flat_transcript = [e for l in hierarchical_transcript for e in l]
			out.write(u" ".join([utt_id] + flat_transcript))
			out.write(u"\n")
