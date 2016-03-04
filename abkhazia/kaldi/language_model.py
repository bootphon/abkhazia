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
import shutil

import abkhazia.utils.basic_io as io
import abkhazia.kaldi.abstract_recipe as abstract_recipe


class LanguageModel(abstract_recipe.AbstractRecipe):
    """Compute a language model from an abkhazia corpus"""
    name = 'language'

    def create(self, args):
        # check we have either word or phone level
        level_choices = ['word', 'phone']
        if args.model_level not in level_choices:
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
        text = self.a2k.setup_text(desired_utts=desired_utts)
        io.cpp_sort(text)

        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        prune_lexicon = True if args.prune_lexicon == 'true' else False
        lm_text = os.path.join(self.a2k._dict_path(), 'lm_text.txt')
        if args.model_level == 'word':
            self.a2k.setup_lexicon(prune_lexicon=prune_lexicon)

            # copy train text to word_bigram for LM estimation
            shutil.copy(text, lm_text)
        else:  # phone level
            lexicon = self.a2k.setup_phone_lexicon()
            io.word2phone(lexicon, text, lm_text)

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
