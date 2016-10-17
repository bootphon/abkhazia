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
"""Options to feed egs/wsj/s5/utils/score.sh

Following score options are ignored: iter, stage, stats. The reverse
option is linked to the mkgraph.reverse option

"""

import abkhazia.utils as utils


def options():
    opt = utils.kaldi.options.make_option

    return {k: v for k, v in (
               opt('decode-mbr', default=False, type=bool,
                   help='maximum bayes risk decoding (confusion network)'),
               # the name of that option in Kaldi is beam, but
               # conflicts with deocde.beam option
               opt('pruning-beam', default=6, type=float,
                   help='Pruning beam (applied after acoustic scaling)'),
               # TODO cause bugs when parsing
               # opt('word-ins-penalty', default=[0.0, 0.5, 1.0], type=list,
               #     help='Word insertion penalities to decode with'),
               opt('min-lmwt', default=9, type=int,
                   help='minumum LM-weight for lattice rescoring'),
               opt('max-lmwt', default=20, type=int,
                   help='maximum LM-weight for lattice rescoring'))}


def format(score_opts, mkgraph_opts):
    # generate option string for scoring
    opts = ' '.join('--{} {}'.format(
        'beam' if n == 'pruning-beam' else n, str(o))
                    for n, o in score_opts.iteritems())

    # add the reverse flag if enabled in the mkgraph options
    if mkgraph_opts['reverse'].value:
        opts += ' --reverse true'
    return opts
