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
Note on model trained with word_position_dependent phones (this is 
the default in kaldi)

The phone-loop lexicon needs to include all position dependent phone variants,
and this is not done correctly by the standard prepare_lang.sh script from kaldi.
To fix this, if word_position_dependent is set to true in the script below, a customized
version of prepare_lang.sh is copied in the 'local' folder of the recipe.
The recipe phone_loop_lm.sh in kaldi_templates uses this prepare_lang.sh if it finds
it in the 'local' folder otherwise the default one (in 'utils') is used. The only difference
between the two prepare_lang.sh is that in the custom script on line 116-120 the 
lexiconp.original is simply copied from lexiconp.txt in the source directory assuming
that word position variants have already been included in it. Accordingly, the script below
generates directly all word position variants in lexicon.txt when word_position_dependent is
true (for example, an entry 'a a' is replaced by 'a_I a_I\n a_B a_B\n a_E a_E\n a_S a_S', etc.).
The language model (G.txt) also uses explicitly the word position variants.

Notes on the structure of prepare_lang.sh in current kaldi version:
	if position_dependent_phones:
		line 116—120: convert lexiconp.txt to lexiconp.original adding word-position markers to phone transcription
		line 136—138: create phone_map.txt that contains all phones including word position variants

		line 205–212: add extra-questions specific to word-position
	
		line 236—240: create word_boundary.txt describing with a word the word position of each phone, standard positions being: nonword, internal, singleton, begin and end.
	else:
		lexiconp.original is just a copy of lexiconp.txt and phone_map a kind of concatenation of silence and nonsilence phones, word_map can be provided externally in source directory (otherwise it is not created)

	line 331—334: if word_boundary.txt exists a word_boundary.int is created

word_boundary.txt, extra_questions.txt and phone_map.txt are generated correctly by the original
prepare_lang.sh in all cases, only lexiconp.original poses problem.
"""

#TODOs

# For now each phone has equal probability (no phonotactics), make this more flexible
# and allow estimating phonotactics from training text or providing it directly from
# an external source. Note that Phonotactics can take the word-position variants into
# account or not (in the latter case, probabilities are shared across variants).

# Put this in a2k as setup_phone_loop ?

# Control for risk of overwriting of lang and split in recipe/data ?

# Check in validate_corpus that adding _I, _B, _E or _S suffixes to words resp.
# phones does not create conflicts, otherwise issue a warning to say that phone-loops LM
# won't work resp. word_position_dependent models won't be usable.

# If word_position_dependent phones are used, need to make sure that the word position markers
# are dropped before scoring for both phones and words.

def setup_phone_loop(corpus_path, recipe_path, name="phone_loop", word_position_dependent=True):
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
	# if word_position_dependent copy custom prepare_lang.sh script to 'local' folder
	shutil.copy(p.join(kaldi_bin_dir, 'kaldi_templates', 'prepare_lang_wpdpl.sh'),\
				p.join(recipe_path, 'local', 'prepare_lang.sh'))
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
	# create explicit word position variants if word_position_dependent
	# Begin, End, Internal and Singleton
	if word_position_dependent:
		phones = [[phone+u"_B", phone+u"_E", phone+u"_I", phone+u"_S"] for phone in phones]
		phones = [phone for phone_variants in phones for phone in phone_variants]
	# add 'phone' lexicon
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'lexicon.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			out.write(u'{0} {1}\n'.format(word, word))
	# describe FST corresponding to desired language model in a text file
	with codecs.open(p.join(recipe_path, 'data', 'local', name, 'G.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			out.write(u'0 1 {0} {1}\n'.format(word, word))
		out.write(u'1 0.0')  # final node
	# note that optional silences are added when composing G with L (lexicon) 
	# when calling prepare_lang.sh, except if silence_prob is set to 0
