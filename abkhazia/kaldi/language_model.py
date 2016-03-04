# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
"""Provides the LanguageModel class"""

import os

import abkhazia.utils.basic_io as io
import abkhazia.kaldi.abstract_recipe as abstract_recipe


# [--prune_lexicon <true|false>]: (default: false) Could be useful
# when using a lexicon that is tailored to the corpus to the point of
# overfitting (i.e. only words occuring in the corpus were included
# and many other common words weren't), which could lead to
# overestimated performance on words from the lexicon appearing in the
# test only.  Removes from the lexicon all words that are not present
# at least once in the training set.
#
# [--level <word|phone>] compute a phone-level or word-level n-gram
class LanguageModel(abstract_recipe.AbstractRecipe):
    """Compute a language model from an abkhazia corpus"""
    name = 'language'

    def create(self, args):
        # check we have either word or phone level
        level_choices = ['word', 'phone']
        if args.level not in level_choices:
            raise RuntimeError(
                'language model level must be in {}, it is {}'
                .format(level_choices, args.level))

        self.log.debug('filtering out utterances shorther than 15ms')
        wav_dir = os.path.join(self.corpus_dir, 'data', 'wavs')
        seg_file = os.path.join(self.corpus_dir, 'data', 'segments.txt')
        utt_durations = io.get_utt_durations(wav_dir, seg_file, args.njobs)
        desired_utts = [utt for utt in utt_durations
                        if utt_durations[utt] >= .015]

        # setup data files common to both levels
        self.a2k.setup_text(desired_utts=desired_utts)
        text = 'that text file'  # TODO
        io.cpp_sort(text)

        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        if args.level == 'word':
            self.a2k.setup_lexicon(prune_lexicon=args.prune_lexicon)

            # copy train text to word_bigram for LM estimation
            train_text = p.join(self.recipe_dir, 'data', 'train', 'text')
            out_dir = self.a2k._dict_path(self.recipe_dir, name='word_bigram')
            shutil.copy(train_text, p.join(out_dir, 'lm_text.txt'))

        else:  # phone level
            # TODO retrieve this from thomas's version
            self.a2k.setup_phone_lexicon()

            lexicon = os.path.join(self.corpus_dir, 'data', 'lexicon.txt')
            text = os.path.join(self.corpus_dir, 'data', 'text.txt')
            out_file = os.path.join(self.a2k._dict_path(), 'lm_text.txt')
            io.word2phone(lexicon, text, out_file)



        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()
        self.a2k.setup_lm_scripts(args)

        run = os.path.join(self.recipe_dir, 'run.sh')
        with open(run, 'w') as out:
            out.write("""#!/bin/bash -u

[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

./local/prepare_lm.sh dict || exit 1
            """)

        # chmod +x run.sh
        os.chmod(run, os.stat(run).st_mode | 0o111)
