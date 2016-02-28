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
    name = 'language_model'

    def create(self, args):
        # DICT folder
        self.a2k.setup_lexicon()
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        lexicon = os.path.join(self.corpus_dir, 'data', 'lexicon.txt')
        text = os.path.join(self.corpus_dir, 'data', 'text.txt')
        out_dir = os.path.join(self.a2k._dict_path(), 'lm_text.txt')
        io.word2phone(lexicon, text, out_dir)

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
