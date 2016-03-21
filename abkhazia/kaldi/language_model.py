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
import textwrap

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

        # setup data files common to both levels
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        desired_utts = self.a2k.desired_utterances(njobs=args.njobs)
        text = self.a2k.setup_text(desired_utts=desired_utts)

        # setup lm lexicon and input text depending on model level
        lm_text = os.path.join(self.a2k._local_path(), 'lm_text.txt')
        lexicon = self.a2k.setup_lexicon()
        if args.model_level == 'word':
            shutil.copy(text, lm_text)
        else:  # phone level
            io.word2phone(lexicon, text, lm_text)
            self.a2k.setup_phone_lexicon()

        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()
        self.a2k.setup_lm_scripts(args)

        run = os.path.join(self.recipe_dir, 'run.sh')
        script = textwrap.dedent('''\
        #!/bin/bash -u
        error_msg="cmd.sh not found. Jobs may not execute properly."
        [ -f cmd.sh ] && source ./cmd.sh || echo $error_msg
        . path.sh || { echo "Cannot source path.sh"; exit 1; }
        ''' + './local/prepare_lm.sh {} || exit 1'.format(self.a2k.name))

        with open(run, 'w') as out:
            out.write(script)

        # chmod +x run.sh
        os.chmod(run, os.stat(run).st_mode | 0o111)

    def export(self):
        """Export data/dict/G.fst in export/language_model.fst"""
        origin = os.path.join(self.recipe_dir, 'data', self.a2k.name, 'G.fst')
        target = os.path.join(self.recipe_dir, 'export', 'language_model.fst')
        self.log.info('writing %s', target)

        dirname = os.path.dirname(target)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        shutil.copy(origin, target)
