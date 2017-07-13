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
"""Wrapper on egs/wsj/s5/utils/mkgraph.sh

Instantiate a full decoding graph (HCLG), 'quinphone' option is
not forwarded from kaldi to abkhazia for now.

"""

import os
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi


def options():
    """Return default parameters for the mkgraph script"""
    opt = kaldi.options.make_option

    return {k: v for k, v in (
        opt('transition-scale', default=1.0, type=float,
            help='Transition-probability scale'),
        opt('self-loop-scale', default=0.1, type=float,
            help='Scale of self-loop versus non-self-loop log probs'),
        opt('reverse', default=False, type=bool,
            help='Build a time-reversed H transducer'))}


def mkgraph(decoder, verbose=True):
    decoder.log.info('computing full decoding graph')

    opts = decoder.mkgraph_opts

    target = os.path.join(decoder.recipe_dir, 'graph')
    if not os.path.isdir(target):
        os.makedirs(target)

    command = (
        '{cmd} {log} utils/mkgraph.sh {mono} {reverse} '
        '--transition-scale {tscale} --self-loop-scale {slscale} '
        '{lang} {model} {graph}'.format(
            cmd=os.path.join(
                'utils', utils.config.get('kaldi', 'highmem-cmd')),
            log=os.path.join(target, 'mkgraph.log'),
            mono='--mono' if decoder.am_type == 'mono' else '',
            reverse='--reverse' if opts['reverse'].value else '',
            tscale=str(opts['transition-scale']),
            slscale=str(opts['self-loop-scale']),
            lang=decoder.lm_dir,
            model=decoder.am_dir,
            graph=target))

    decoder._run_command(command, verbose=verbose)

    return target
