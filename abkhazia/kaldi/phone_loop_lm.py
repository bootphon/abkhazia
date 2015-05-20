# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

import os.path as p
import codecs
import shutil
import abkhazia.kaldi.abkhazia2kaldi as a2k 

#########################################################
# Generate a phone-loop language model for use in kaldi #
#########################################################

"""
This script copies a phone_loop_lm.sh script in the local folder of the target recipe,
whose execution will create a language model folder, that can be used within the recipe
to combine any acoustic model with a phone-level language model for decoding. 

Before running phone_loop_lm.sh, check that the options in the script correspond to your 
setup and modify them as needed. For example, to use models with word_position_dependent
phones (this is the default in kaldi) set the word_position_dependent option in phone_loop_lm.sh
to true.

Note on model trained with word_position_dependent phones (this is 
the default in kaldi): 

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

# phone_loop_lm.sh should not be able to fail silently.

# For now each phone has equal probability (no phonotactics), make this more flexible
# and allow estimating phonotactics from training text or providing it directly from
# an external source.

# Not sure how to get a language models on triphones or word-position-dependent variants
# or if it even makes sense. I think it can only be done easily within kaldi if triphones
# or word-position-dependent variants are output labels (i.e. words), but for triphones this
# would conflict with the C expansion step in HCLG and for word-position-dependent variants
# this poses problem at the lattice stage, where lattices become big and word-position
# variants are considered as different decodings, which they shouldn't…
# Probably the clean solution to specify a LM on allophonic variants would be to modify the 
# C step (in HCLG) to allow an expansion weighted by a given LM. This means meddling inside
# kaldi code, so we won't do it unless we really really need it.

# Put this in a2k as setup_phone_loop ?

# Control for risk of overwriting of lang and split in recipe/data ?

# Check in validate_corpus that adding _I, _B, _E or _S suffixes to
# phones does not create conflicts, otherwise issue a warning to say that 
# word_position_dependent models won't be usable.

def setup_phone_loop(corpus_path, recipe_path, name="phone_loop"):
	"""
	recipe_path: e.g. "/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/kaldi/GP_Mandarin/train_and_decode/s5"
	lang_dir: e.g. "phone_loop"
			Will copy kaldi template'phone_loop_lm.sh' in 'recipe_path/local'
			and create a directory 'recipe_path/data/local/name'
			that can be passed as an argument to 'phone_loop_lm.sh'
			'phone_loop_lm.sh' can then be called to create a directory
			'recipe_path/data/name' that can be passed as the 'lm' argument
			to 'train_and_decode.sh'.
	"""
	# copy kaldi template'phone_loop_lm.sh' in 'recipe_path/local'
	kaldi_bin_dir = p.dirname(p.realpath(__file__))
	shutil.copy(p.join(kaldi_bin_dir, 'kaldi_templates', 'phone_loop_lm.sh'),\
				p.join(recipe_path, 'local', 'phone_loop_lm.sh'))
	# copy custom prepare_lang.sh script to 'local' folder
	# this script is used for models trained with word_position_dependent phone variants
	shutil.copy(p.join(kaldi_bin_dir, 'kaldi_templates', 'prepare_lang_wpdpl.sh'),\
				p.join(recipe_path, 'local', 'prepare_lang_wpdpl.sh'))
	shutil.copy(p.join(kaldi_bin_dir, 'kaldi_templates', 'validate_lang_wpdpl.pl'),\
				p.join(recipe_path, 'local', 'validate_lang_wpdpl.pl'))
	# setup lang folder for phone loop with phones 
	a2k.setup_phones(corpus_path, recipe_path, name)  # nonsilence_phones.txt
	a2k.setup_silences(corpus_path, recipe_path, name)  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(corpus_path, recipe_path, name)  # extra_questions.txt
	# get list of phones (including silence and non-silence phones)
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'nonsilence_phones.txt'),\
					 mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	phones = [line.strip() for line in lines]
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'silence_phones.txt'),\
					 mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	phones = phones + [line.strip() for line in lines]
	# create 'phone' lexicon
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'lexicon.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			out.write(u'{0} {1}\n'.format(word, word))
		# add <unk> word, in case one wants to use the phone loop lexicon for training
		# it also is necessary if one doesn't want to modify the validating scripts too much
		out.write(u'<unk> SPN\n')
	# describe FST corresponding to desired language model in a text file
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'G.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			# should I, C++ sort the created files ?
			out.write(u'0 0 {0} {1}\n'.format(word, word))
		out.write(u'0 0.0')  # final node
	# note that optional silences are added when composing G with L (lexicon) 
	# when calling prepare_lang.sh, except if silence_prob is set to 0


#setup_phone_loop("", recipe_path, name="phone_loop")
