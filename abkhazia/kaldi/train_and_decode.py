# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

"""
This script takes a corpus in abkhazia format
which has been splitted into a train and a test part
and instantiates a kaldi recipe to train
a standard speaker-adapted triphone HMM-GMM model
on the train part and output various kind of decodings
of the test part.

See the recipe template in kaldi_templates/train_and_decode.sh.
See in particular the arguments that can be passed to the
recipe and their default values.

Once the recipe is instantiated it can be ran like any other kaldi
recipe.
"""


import os.path as p
import os
import shutil
import abkhazia.utilities.basic_io as io
import abkhazia.kaldi.abkhazia2kaldi as a2k 

# Main function of this module: 'create_kaldi_recipe'
# TODO: 
#	- document the input and output of create_kaldi_recipe
#	- document the input and output of the created recipe and how to run it
#	- write a command-line interface to create_kaldi_recipe


def create_kaldi_recipe(corpus_path, output_path, kaldi_root,
					recipe_name="train_and_decode",																			
					train_name='train', test_name='test',
					prune_lexicon=False):
	"""
	Function to instantiate a ready-to-use kaldi recipe from a speech
	corpora in abkhazia format

	Parameters:
		corpus_path: string
		output_path: string
		kaldi_root: string
		recipe_name: string (default: 'train_and_decode')
		train_name: string (default: 'train')
		test_name: string (default: 'test')
			Note that the names of the splits in the resulting recipe will always
			be train and test irrespective of the values of these arguments
		prune_lexicon: boolean (default: False)
			Could be useful when using a lexicon that is tailored to the corpus
			to the point of overfitting (i.e. only words occuring in the corpus
			were included and many other common words weren't), which could lead
			to overestimated performance on words from the lexicon appearing in
			the test only.
			Removes from the lexicon all words that are not present at least 
			once in the training set.
	"""
	# Checking paths
	assert p.isdir(corpus_path), "Directory doesn't exist: {0}".format(corpus_path)
	recipe_path = p.join(output_path, recipe_name, 's5')
	if p.isdir(recipe_path):
		raise IOError("Directory already exists: {0}".format(recipe_path))
	else:
		os.makedirs(recipe_path)
	# DICT folder (common to all splits)
	a2k.setup_lexicon(corpus_path, recipe_path, prune_lexicon, train_name)  # lexicon.txt
	a2k.setup_phones(corpus_path, recipe_path)  # nonsilence_phones.txt
	a2k.setup_silences(corpus_path, recipe_path)  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(corpus_path, recipe_path)  # extra_questions.txt
	# DATA folders (split specific)
	for in_split, out_split in zip([train_name, test_name], ['train', 'test']):
		# find utterances that are too short for kaldi (less than 15ms)
		# (they result in empty feature files that trigger kaldi warnings)
		# in order to filter them out of the text, utt2spk, segments and wav.scp files
		wav_dir = os.path.join(corpus_path, 'data', 'wavs')
		seg_file = os.path.join(corpus_path, 'data', 'split', in_split, 'segments.txt')
		utt_durations = io.get_utt_durations(wav_dir, seg_file)
		desired_utts = [utt for utt in utt_durations if utt_durations[utt] >= .015]
		# setup data files
		a2k.setup_text(corpus_path, recipe_path, in_split, out_split, desired_utts)  # text
		a2k.setup_utt2spk(corpus_path, recipe_path, in_split, out_split, desired_utts)  # utt2spk
		a2k.setup_segments(corpus_path, recipe_path, in_split, out_split, desired_utts)  # segments
		a2k.setup_wav(corpus_path, recipe_path, in_split, out_split, desired_utts)  # wav.scp
		# do some cpp_sorting just to be sure (for example if the abkhazia corpus has
		# been copied to a different machine after its creation, there might be 
		# some machine-dependent differences in the required orders)
		files = ['text', 'utt2spk', 'segments', 'wav.scp']
		for f in files:
			path = p.join(recipe_path, 'data', out_split, f)
			if p.exists(path):
				io.cpp_sort(path)
	# LM folders (common to all splits)
	# for now just have word- and phone-level bigrams estimated from train split
	# word-level bigram (at this point it could be n-gram actually)
	a2k.setup_lexicon(corpus_path, recipe_path, prune_lexicon, train_name, name='word_bigram')  # lexicon.txt
	a2k.setup_phones(corpus_path, recipe_path, name='word_bigram')  # nonsilence_phones.txt
	a2k.setup_silences(corpus_path, recipe_path, name='word_bigram')  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(corpus_path, recipe_path, name='word_bigram')  # extra_questions.txt
	# copy train text to word_bigram for LM estimation
	train_text = p.join(recipe_path, 'data', 'train', 'text')
	out_dir = a2k.get_dict_path(recipe_path, name='word_bigram')
	shutil.copy(train_text, p.join(out_dir, 'lm_text.txt'))
	# phone-level bigram (at this point it could be n-gram actually)
	a2k.setup_phones(corpus_path, recipe_path, name='phone_bigram')  # nonsilence_phones.txt
	a2k.setup_silences(corpus_path, recipe_path, name='phone_bigram')  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(corpus_path, recipe_path, name='phone_bigram')  # extra_questions.txt
	a2k.setup_phone_lexicon(corpus_path, recipe_path, name='phone_bigram')  # lexicon.txt
	# copy phone version of train text to phone_bigram for LM estimation
	lexicon = p.join(corpus_path, 'data', 'lexicon.txt')
	text = p.join(corpus_path, 'data', 'split', train_name, 'text.txt')
	out_dir = a2k.get_dict_path(recipe_path, name='phone_bigram')
	io.word2phone(lexicon, text, p.join(out_dir, 'lm_text.txt'))	
	# create empty 'phone' file, just to indicate the LM is phone_level
	with open(p.join(out_dir, 'phone'), 'w'):
		pass
	# Other files and folders (common to all splits)
	a2k.setup_wav_folder(corpus_path, recipe_path)  # wav folder
	a2k.setup_kaldi_folders(kaldi_root, recipe_path)  # misc. kaldi symlinks, directories and files 
	a2k.setup_machine_specific_scripts(recipe_path)  # path.sh, cmd.sh
	a2k.setup_main_scripts(recipe_path, 'train_and_decode.sh')  # score.sh, run.sh
	a2k.setup_lm_scripts(recipe_path)
	

"""
For future reference: creating a phone-loop G.txt:
	# describe FST corresponding to desired language model in a text file
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'G.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			# should I, C++ sort the created files ?
			out.write(u'0 0 {0} {1}\n'.format(word, word))
		out.write(u'0 0.0')  # final node
	# note that optional silences are added when composing G with L (lexicon) 
	# when calling prepare_lang.sh, except if silence_prob is set to 0
"""
