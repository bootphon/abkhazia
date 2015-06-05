# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

import abkhazia.utilities.basic_io as io
import codecs
import os.path as p

def convert_text(corpus_path, train_out, test_out, train_name='train', test_name='test'):
	"""
	Create 'phone' version of text.txt (transcription of text directly into phones, without
	any word boundary marker). This is used to estimate phone-level n-gram language models
	for use with kaldi recipes.
	For OOVs: just drop the whole sentence for now.
	#TODO check if this should be affected in anyway when lexicon is pruned from test only
	words
	"""
	lexicon = p.join(corpus_path, 'data', 'lexicon.txt')
	words, transcriptions = io.read_dictionary(lexicon)
	dictionary = {}
	for word, transcript in zip(words, transcriptions):
		dictionary[word] = transcript
	train_text = p.join(corpus_path, 'data', 'split', train_name, 'text.txt')
	test_text = p.join(corpus_path, 'data', 'split', test_name, 'text.txt')
	word2phone(dictionary, train_text, train_out)
	word2phone(dictionary, test_text, test_out)


def word2phone(dictionary, text_file, out_file):
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


corpus = "/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/GP_Mandarin"
out_folder = "/Users/thomas/Documents/PhD/Recherche/test"
convert_text(corpus, p.join(out_folder, 'train.txt'), p.join(out_folder, 'test.txt'))



	


