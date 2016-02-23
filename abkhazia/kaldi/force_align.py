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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Provides the ForceAlign class"""

import os

import abkhazia.utils.basic_io as io
import abkhazia.kaldi.abstract_recipe as abstract_recipe

class ForceAlign(abstract_recipe.AbstractRecipe):
    """Compute forced alignment of an abkhazia corpus

    Takes a corpus in abkhazia format and instantiates a kaldi recipe
    to train a standard speaker-adapted triphone HMM-GMM model on the
    whole corpus and generate a forced alignment.

    See the recipe template in kaldi_templates/force_align.sh.  See in
    particular the arguments that can be passed to the recipe and
    their default values.

    """
    name = 'force_align'

    def create(self):
        # DICT folder
        self.a2k.setup_lexicon()
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # DATA folders. Find utterances that are too short for kaldi
        # (less than 15ms) (they result in empty feature files that
        # trigger kaldi warnings) in order to filter them out of the
        # text, utt2spk, segments and wav.scp files
        wav_dir = os.path.join(self.corpus_dir, 'data', 'wavs')
        seg_file = os.path.join(self.corpus_dir, 'data', 'segments.txt')
        utt_durations = io.get_utt_durations(wav_dir, seg_file)
        desired_utts = [utt for utt in utt_durations
                        if utt_durations[utt] >= .015]

        # setup data files
        self.a2k.setup_text(desired_utts=desired_utts)
        self.a2k.setup_utt2spk(desired_utts=desired_utts)
        self.a2k.setup_segments(desired_utts=desired_utts)
        self.a2k.setup_wav(desired_utts=desired_utts)

        # do some cpp_sorting just to be sure (for example if the
        # abkhazia corpus has been copied to a different machine after
        # its creation, there might be some machine-dependent
        # differences in the required orders)
        files = ['text', 'utt2spk', 'segments', 'wav.scp']
        for target in files:
            path = os.path.join(self.recipe_dir, 'data', 'main', target)
            if os.path.exists(path):
                io.cpp_sort(path)

        # Other files and folders (common to all splits)
        self.a2k.setup_wav_folder()
        # misc. kaldi symlinks, directories and files
        self.a2k.setup_kaldi_folders()
        # path.sh, cmd.sh
        self.a2k.setup_machine_specific_scripts()
        # score.sh, run.sh
        self.a2k.setup_main_scripts('force_align.sh')
