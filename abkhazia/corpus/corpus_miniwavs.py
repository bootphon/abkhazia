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
"""Provides the CorpusMiniWavs class"""

import ConfigParser
import random
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import shlex
import os
import shutil
import wave
import contextlib

from operator import itemgetter
from math import exp
from abkhazia.utils import logger, config


class CorpusMiniWavs(object):
    """A class that creates n seconds files of speech (using a VAD in input)
    and lists the usable triphones in each file.
