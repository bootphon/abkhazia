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


def create_kaldi_recipe(train_corpus, test_corpus, output_path,
					kaldi_root,
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
	assert p.isdir(train_corpus), "Directory doesn't exist: {0}".format(train_corpus)
	assert p.isdir(test_corpus), "Directory doesn't exist: {0}".format(test_corpus)
	recipe_path = p.join(output_path, recipe_name)
	if p.isdir(recipe_path):
		raise IOError("Directory already exists: {0}".format(recipe_path))
	else:
		os.makedirs(recipe_path)
	# DICT folder (common to all splits)
	a2k.setup_lexicon(train_corpus, recipe_path, prune_lexicon, train_name)  # lexicon.txt
	a2k.setup_phones(train_corpus, recipe_path)  # nonsilence_phones.txt
	a2k.setup_silences(train_corpus, recipe_path)  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(train_corpus, recipe_path)  # extra_questions.txt
	# DATA folders (split specific)
	for corpus, out_split in zip([train_corpus, test_corpus], ['train', 'test']):
		# find utterances that are too short for kaldi (less than 15ms)
		# (they result in empty feature files that trigger kaldi warnings)
		# in order to filter them out of the text, utt2spk, segments and wav.scp files
		wav_dir = os.path.join(corpus, 'wavs')
		seg_file = os.path.join(corpus, 'segments.txt')
		utt_durations = io.get_utt_durations(wav_dir, seg_file)
		desired_utts = [utt for utt in utt_durations if utt_durations[utt] >= .015]
		# setup data files
		a2k.setup_text(corpus, recipe_path, out_split, desired_utts)  # text
		a2k.setup_utt2spk(corpus, recipe_path, out_split, desired_utts)  # utt2spk
		a2k.setup_segments(corpus, recipe_path, out_split, desired_utts)  # segments
		a2k.setup_wav(corpus, recipe_path, out_split, desired_utts)  # wav.scp
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
	a2k.setup_lexicon(train_corpus, recipe_path, prune_lexicon, train_name, name='word_bigram')  # lexicon.txt
	a2k.setup_phones(train_corpus, recipe_path, name='word_bigram')  # nonsilence_phones.txt
	a2k.setup_silences(train_corpus, recipe_path, name='word_bigram')  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(train_corpus, recipe_path, name='word_bigram')  # extra_questions.txt
	# copy train text to word_bigram for LM estimation
	train_text = p.join(recipe_path, 'data', 'train', 'text')
	out_dir = a2k.get_dict_path(recipe_path, name='word_bigram')
	shutil.copy(train_text, p.join(out_dir, 'lm_text.txt'))
	# phone-level bigram (at this point it could be n-gram actually)
	a2k.setup_phones(train_corpus, recipe_path, name='phone_bigram')  # nonsilence_phones.txt
	a2k.setup_silences(train_corpus, recipe_path, name='phone_bigram')  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(train_corpus, recipe_path, name='phone_bigram')  # extra_questions.txt
	a2k.setup_phone_lexicon(train_corpus, recipe_path, name='phone_bigram')  # lexicon.txt
	# copy phone version of train text to phone_bigram for LM estimation
	lexicon = p.join(train_corpus, 'lexicon.txt')
	text = p.join(train_corpus, 'text.txt')
	out_dir = a2k.get_dict_path(recipe_path, name='phone_bigram')
	io.word2phone(lexicon, text, p.join(out_dir, 'lm_text.txt'))	
	# create empty 'phone' file, just to indicate the LM is phone_level
	with open(p.join(out_dir, 'phone'), 'w'):
		pass
	# Other files and folders (common to all splits)
	a2k.setup_wav_folder(train_corpus, recipe_path)  # wav folder
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

"""
Note on phone-level language models for acoustic models trained with word_position_dependent
phones (this is the default in kaldi): 

A customized version of prepare_lang.sh is copied in the 'local' folder of the recipe,
by this script. This version creates appropriate word_position_dependent pronunciation
variants for the 'phone' lexicon.
The recipe phone_loop_lm.sh in kaldi_templates uses this prepare_lang.sh when its
word_position_dependent option is set to true, otherwise the default prepare_lang.sh
(in 'utils') is used. As a result of this customization the script validate_lang.pl also
needs to be slightly amended and a custom version is also copied by in the 
local folder and used by the custom prepare_lang.sh.
"""

#TODOs

# prepare_lm.sh should not be able to fail silently.

# Not sure how to get a language models on triphones or word-position-dependent variants
# or if it even makes sense. I think it can only be done easily within kaldi if triphones
# or word-position-dependent variants are output labels (i.e. words), but for triphones this
# would conflict with the C expansion step in HCLG and for word-position-dependent variants
# this poses problem at the lattice stage, where lattices become big and word-position
# variants are considered as different decodings, which they shouldn't…
# Probably the clean solution to specify a LM on allophonic variants would be to modify the 
# C step (in HCLG) to allow an expansion weighted by a given LM. This means meddling inside
# kaldi code, so we won't do it unless we really really need it.

# Control for risk of overwriting of lang and split in recipe/data ? (this folder contains both
# the splits and the LMs)

# Check in validate_corpus that adding _I, _B, _E or _S suffixes to
# phones does not create conflicts, otherwise issue a warning to say that 
# word_position_dependent models won't be usable.
