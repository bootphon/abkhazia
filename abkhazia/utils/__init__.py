# -*- coding: utf-8 -*-
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
"""This package provides various utilities to abkhazia"""

from .path import *
from .misc import *
from .config import config, AbkhaziaConfig

import abkhazia.utils.abkhazia_base as abkhazia_base
import abkhazia.utils.logger as logger
import abkhazia.utils.wav as wav
import abkhazia.utils.jobs as jobs
import abkhazia.utils.cha as cha
