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

"""Provides tools for preparation of the corpora supported in abkhazia

Each supported corpus have its own data preparation script in
this package.

"""

from .abstract_preparator import AbstractPreparator, AbstractPreparatorWithCMU

from .aic_preparator import AICPreparator
from .buckeye_preparator import BuckeyePreparator
from .childes_preparator import ChildesPreparator
from .csj_preparator import CSJPreparator
from .librispeech_preparator import LibriSpeechPreparator
from .xitsonga_preparator import XitsongaPreparator

from .globalphone_abstract_preparator import (
    AbstractGlobalPhonePreparator)
from .globalphone_mandarin_preparator import (
    MandarinPreparator)
from .globalphone_vietnamese_preparator import (
    VietnamesePreparator)

from .wsj_preparator import (
    WallStreetJournalPreparator,
    JournalistReadPreparator,
    JournalistSpontaneousPreparator,
    MainReadPreparator)
