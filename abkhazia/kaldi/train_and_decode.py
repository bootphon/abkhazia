# coding: utf-8

# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard#
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Provides the TrainDecode class"""

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

"""

import os
import shutil

import abkhazia.utils.basic_io as io
import abkhazia.kaldi.abstract_recipe as abstract_recipe

class TrainDecode(abstract_recipe.AbstractRecipe):
    """Instantiate a ready-to-use kaldi recipe from an abkhazia corpus

    train_name: string (default: 'train')

    test_name: string (default: 'test')

    Note that the names of the splits in the resulting recipe will
    always be train and test irrespective of the values of these
    arguments

    prune_lexicon: boolean (default: False) Could be useful when using
      a lexicon that is tailored to the corpus to the point of
      overfitting (i.e. only words occuring in the corpus were
      included and many other common words weren't), which could lead
      to overestimated performance on words from the lexicon appearing
      in the test only.  Removes from the lexicon all words that are
      not present at least once in the training set.

    """
    name = 'train_and_decode'

    def __init__(self, corpus_dir, recipe_dir=None, verbose=False,
                 train_name='train', test_name='test', prune_lexicon=False):
        super(TrainDecode, self).__init__(corpus_dir, recipe_dir, verbose)
        self.train = train_name
        self.test = test_name
        self.prune_lexicon = prune_lexicon

    def create(self):
        # DICT folder (common to all splits)
        self.a2k.setup_lexicon(self.prune_lexicon, self.train)
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # DATA folders (split specific)
        for in_split, out_split in zip([self.train, self.test],
                                       ['train', 'test']):
            # find utterances that are too short for kaldi (less than
            # 15ms) (they result in empty feature files that trigger
            # kaldi warnings) in order to filter them out of the text,
            # utt2spk, segments and wav.scp files
            wav_dir = os.path.join(self.corpus_dir, 'data', 'wavs')
            seg_file = os.path.join(
                self.corpus_dir, 'data', 'split', in_split, 'segments.txt')
            utt_durations = io.get_utt_durations(wav_dir, seg_file)
            desired_utts = [utt for utt in utt_durations
                            if utt_durations[utt] >= .015]

            # setup data files
            self.a2k.setup_text(in_split, out_split, desired_utts)
            self.a2k.setup_utt2spk(in_split, out_split, desired_utts)
            self.a2k.setup_segments(in_split, out_split, desired_utts)
            self.a2k.setup_wav(in_split, out_split, desired_utts)

            # do some cpp_sorting just to be sure (for example if the
            # abkhazia corpus has been copied to a different machine
            # after its creation, there might be some
            # machine-dependent differences in the required orders)
            files = ['text', 'utt2spk', 'segments', 'wav.scp']
            for target in files:
                path = os.path.join(self.recipe_dir, 'data', out_split, target)
                if os.path.exists(path):
                    io.cpp_sort(path)

        # LM folders (common to all splits) for now just have word-
        # and phone-level bigrams estimated from train split
        # word-level bigram (at this point it could be n-gram
        # actually)
        self.a2k.setup_lexicon(
            self.prune_lexicon, self.train, name='word_bigram')
        self.a2k.setup_phones(name='word_bigram')
        self.a2k.setup_silences(name='word_bigram')
        self.a2k.setup_variants(name='word_bigram')

        # copy train text to word_bigram for LM estimation
        train_text = os.path.join(self.recipe_dir, 'data', 'train', 'text')
        out_dir = self.a2k._dict_path(name='word_bigram')
        shutil.copy(train_text, os.path.join(out_dir, 'lm_text.txt'))

        # phone-level bigram (at this point it could be n-gram actually)
        self.a2k.setup_phones(name='phone_bigram')
        self.a2k.setup_silences(name='phone_bigram')
        self.a2k.setup_variants(name='phone_bigram')
        self.a2k.setup_phone_lexicon(name='phone_bigram')

        # copy phone version of train text to phone_bigram for LM estimation
        lexicon = os.path.join(self.corpus_dir, 'data', 'lexicon.txt')
        text = os.path.join(
            self.corpus_dir, 'data', 'split', self.train, 'text.txt')
        out_dir = self.a2k._dict_path(name='phone_bigram')
        io.word2phone(lexicon, text, os.path.join(out_dir, 'lm_text.txt'))

        # create empty 'phone' file, just to indicate the LM is phone_level
        with open(os.path.join(out_dir, 'phone'), 'w'):
            pass

        # Other files and folders (common to all splits)
        self.a2k.setup_wav_folder()
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()
        self.a2k.setup_main_scripts('train_and_decode.sh')
        self.a2k.setup_lm_scripts()


# For future reference: creating a phone-loop G.txt:
# # describe FST corresponding to desired language model in a text file
# with codecs.open(p.join(recipe_path, 'data', 'local', name, 'G.txt'),\
#                  mode='w', encoding="UTF-8") as out:
#         for word in phones:
#                 # should I, C++ sort the created files ?
#                 out.write(u'0 0 {0} {1}\n'.format(word, word))
#         out.write(u'0 0.0')  # final node
# # note that optional silences are added when composing G with L (lexicon)
# # when calling prepare_lang.sh, except if silence_prob is set to 0

# Note on phone-level language models for acoustic models trained with
# word_position_dependent phones (this is the default in kaldi):

# A customized version of prepare_lang.sh is copied in the 'local'
# folder of the recipe, by this script. This version creates
# appropriate word_position_dependent pronunciation variants for the
# 'phone' lexicon.  The recipe phone_loop_lm.sh in kaldi_templates
# uses this prepare_lang.sh when its word_position_dependent option is
# set to true, otherwise the default prepare_lang.sh (in 'utils') is
# used. As a result of this customization the script validate_lang.pl
# also needs to be slightly amended and a custom version is also
# copied by in the local folder and used by the custom
# prepare_lang.sh.

# TODO

# prepare_lm.sh should not be able to fail silently.

# Not sure how to get a language models on triphones or
# word-position-dependent variants or if it even makes sense. I think
# it can only be done easily within kaldi if triphones or
# word-position-dependent variants are output labels (i.e. words), but
# for triphones this would conflict with the C expansion step in HCLG
# and for word-position-dependent variants this poses problem at the
# lattice stage, where lattices become big and word-position variants
# are considered as different decodings, which they shouldn't…
# Probably the clean solution to specify a LM on allophonic variants
# would be to modify the C step (in HCLG) to allow an expansion
# weighted by a given LM. This means meddling inside kaldi code, so we
# won't do it unless we really really need it.

# Check in validate_corpus that adding _I, _B, _E or _S suffixes to
# phones does not create conflicts, otherwise issue a warning to say
# that word_position_dependent models won't be usable.
