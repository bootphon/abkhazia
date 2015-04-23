# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

"""
This script takes a corpus in abkhazia format
and instantiates a kaldi recipe to train
a standard speaker-adapted triphone HMM-GMM model
on the whole corpus and generate a forced alignment.

See the recipe template in kaldi_templates/force_align.sh.
See in particular the arguments that can be passed to the
recipe and their default values.

Once the recipe is instantiated, it can be ran like any
other kaldi recipe.
"""

import os.path as p
import os
import abkhazia.utilities.basic_io as io
import abkhazia.kaldi.abkhazia2kaldi as a2k 

# Main function of this module: 'create_kaldi_recipe'
# TODO: 
#	- document the input and output of create_kaldi_recipe
#	- document the input and output of the created recipe and how to run it
#	- write a command-line interface to create_kaldi_recipe


def create_kaldi_recipe(corpus_path, output_path, kaldi_root,
					recipe_name="force_align"):
	"""
	Function to instantiate a ready-to-use kaldi recipe from a speech
	corpora in abkhazia format

	Parameters:
		corpus_path: string
		output_path: string
		kaldi_root: string
		recipe_name: string (default: 'force_align')
	"""
	# Checking paths
	assert p.isdir(corpus_path), "Directory doesn't exist: {0}".format(corpus_path)
	recipe_path = p.join(output_path, recipe_name, 's5')
	if p.isdir(recipe_path):
		raise IOError("Directory already exists: {0}".format(recipe_path))
	else:
		os.makedirs(recipe_path)
	# DICT folder
	a2k.setup_lexicon(corpus_path, recipe_path)  # lexicon.txt
	a2k.setup_phones(corpus_path, recipe_path)  # nonsilence_phones.txt
	a2k.setup_silences(corpus_path, recipe_path)  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(corpus_path, recipe_path)  # extra_questions.txt
	# DATA folders
	# find utterances that are too short for kaldi (less than 15ms)
	# (they result in empty feature files that trigger kaldi warnings)
	# in order to filter them out of the text, utt2spk, segments and wav.scp files
	wav_dir = os.path.join(corpus_path, 'data', 'wavs')
	seg_file = os.path.join(corpus_path, 'data', 'segments.txt')
	utt_durations = io.get_utt_durations(wav_dir, seg_file)
	desired_utts = [utt for utt in utt_durations if utt_durations[utt] >= .015]
	# setup data files
	a2k.setup_text(corpus_path, recipe_path, desired_utts=desired_utts)  # text
	a2k.setup_utt2spk(corpus_path, recipe_path, desired_utts=desired_utts)  # utt2spk
	a2k.setup_segments(corpus_path, recipe_path, desired_utts=desired_utts)  # segments
	a2k.setup_wav(corpus_path, recipe_path, desired_utts=desired_utts)  # wav.scp
	# do some cpp_sorting just to be sure (for example if the abkhazia corpus has
	# been copied to a different machine after its creation, there might be 
	# some machine-dependent differences in the required orders)
	files = ['text', 'utt2spk', 'segments', 'wav.scp']
	for f in files:
		path = p.join(recipe_path, 'data', 'main', f)
		if p.exists(path):
			io.cpp_sort(path)
	# Other files and folders (common to all splits)
	a2k.setup_wav_folder(corpus_path, recipe_path)  # wav folder
	a2k.setup_kaldi_folders(kaldi_root, recipe_path)  # misc. kaldi symlinks, directories and files 
	a2k.setup_machine_specific_scripts(recipe_path)  # path.sh, cmd.sh
	a2k.setup_main_scripts(recipe_path, 'force_align.sh')  # score.sh, run.sh
