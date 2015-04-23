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

Note that the user has to externally provide a language
model in FST format to be able to run the decoding part
of the resulting recipe. This can be obtained, for example,
using: ...

Once the recipe is instantiated and a language model has
been supplied, it can be ran like any other kaldi
recipe.
"""


import shutil
import os.path as p
import os
import codecs
import subprocess
import abkhazia.utilities.io as io
import abkhazia.kaldi.abkhazia2kaldi as a2k 

# Main function of this module: 'create_kaldi_recipe'
# TODO: 
#	- document the input and output of create_kaldi_recipe
#	- document the input and output of the created recipe and how to run it
#	- write a command-line interface to create_kaldi_recipe


def create_kaldi_recipe(corpus_path, output_path, kaldi_root,
					recipe_name="train_and_decode",																			
					train_name='train', test_name='test',
					prune_lexicon):
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
	# Other files and folders (common to all splits)
	a2k.setup_wav_folder(corpus_path, recipe_path)  # wav folder
	a2k.setup_kaldi_folders(kaldi_root, recipe_path)  # misc. kaldi symlinks, directories and files 
	a2k.setup_machine_specific_scripts(recipe_path)  # path.sh, cmd.sh
	a2k.setup_main_scripts(recipe_path)  # score.sh, run.sh
