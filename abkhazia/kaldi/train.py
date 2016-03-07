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
"""Provides the AcousticModel class"""


import abkhazia.utils.basic_io as io
import abkhazia.kaldi.abstract_recipe as abstract_recipe

class AcousticModel(abstract_recipe.AbstractRecipe):
    """Compute an acoustic model from an abkhazia corpus

    Takes a corpus in abkhazia format and instantiates a kaldi recipe
    to train a standard speaker-adapted triphone HMM-GMM model on the
    whole corpus.

    """
    name = 'train'

    def create(self, args):
        # local folder
        self.a2k.setup_lexicon()
        self.a2k.setup_phones()
        self.a2k.setup_silences()
        self.a2k.setup_variants()

        # setup data files
        desired_utts = self.a2k.desired_utterances(njobs=args.njobs)
        self.a2k.setup_text(desired_utts=desired_utts, out_split=args.name)
        self.a2k.setup_utt2spk(desired_utts=desired_utts, out_split=args.name)
        self.a2k.setup_segments(desired_utts=desired_utts, out_split=args.name)
        self.a2k.setup_wav(desired_utts=desired_utts, out_split=args.name)

        # setup other files and folders
        self.a2k.setup_wav_folder()
        self.a2k.setup_kaldi_folders()
        self.a2k.setup_machine_specific_scripts()

        # setup score.sh and run.sh
        self.a2k.setup_main_scripts('train.sh.in', args)
