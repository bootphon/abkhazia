# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Provides classes for training acoustic models with Kaldi

Four types of acoustic models, of increasing complexity, are
implemented. Running model `n` needs `n-1` to be computed.

(0- Features)
1- Monophone GMM
2- Triphone speaker independent HMM-GMM
3- Triphone speaker adapted HMM-GMM
4- Triphone HMM-DNN

Each model is implemented as a child class of AcousticModelBase, which
is a wrapper to a standard Kaldi recipe in egs/wsj/s5/steps. Each
class forward the parameters of the Kaldi scripts it relies on in an
`options` attribute.

Exemple:
--------

Compute a monophone model with custom parameters

.. python

    am_mono = Monophone(corpus, lm_dir, feats_dir, am_mono_dir)
    am_mono.set_option('num-iterations', 4)
    am_mono.set_option('total-gaussians', 100)
    am_mono.set_option('realign-iterations', [1, 2, 3])
    am_mono.compute()

Access to the list of available options

.. python

   am_tri = Triphone(corpus, lm_dir, am_mono_dir, am_tri_dir)
   for name, entry in am_mono.options.iteritems():
       print name, entry.value, entry.help, entry.default, entry.type


"""

from abkhazia.models.acoustic.monophone import Monophone
from abkhazia.models.acoustic.triphone import Triphone
from abkhazia.models.acoustic.triphone_speaker_adaptive import (
    TriphoneSpeakerAdaptive)
from abkhazia.models.acoustic.neural_network import NeuralNetwork
