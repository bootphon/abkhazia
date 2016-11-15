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
"""Provides implememtations of the abkhazia command line tools

Each abkhazia subcommand is defined here in its own module.

Note that this package contains only the code related to abkhazia
execution from a terminal. It defines argument parsers and delegates
the processing to modules in abkhazia.prepare or abkhazia.kaldi

"""

from abkhazia.commands.abstract_command import AbstractCommand
from abkhazia.commands.abkhazia_acoustic import AbkhaziaAcoustic
from abkhazia.commands.abkhazia_align import AbkhaziaAlign
from abkhazia.commands.abkhazia_language import AbkhaziaLanguage
from abkhazia.commands.abkhazia_decode import AbkhaziaDecode
from abkhazia.commands.abkhazia_prepare import AbkhaziaPrepare
from abkhazia.commands.abkhazia_split import AbkhaziaSplit
from abkhazia.commands.abkhazia_filter import AbkhaziaFilter
from abkhazia.commands.abkhazia_features import AbkhaziaFeatures
from abkhazia.commands.abkhazia_triphones import AbkhaziaTriphones
from abkhazia.commands.abkhazia_split_challenge import AbkhaziaSplitChallenge
from abkhazia.commands.abkhazia_mergewavs import AbkhaziaMergeWavs
