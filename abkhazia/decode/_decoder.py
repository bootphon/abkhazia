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
"""Wrapper on egs/wsj/s5/steps/decode.sh

Following decode options are ignored: num_thread, skip_scoring, iter,
transform_dir

"""

import os
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi
import _score


def options():
    """Return default parameters for the decode script"""
    opt = kaldi.options.make_option

    return {k: v for k, v in (
        opt('acwt', default=0.083333, type=float,
            help=('Acoustic scale used for lattice generation. note: '
                  'only really affects pruning (scoring is on lattices)')),
        opt('max-active', default=7000, type=int,
            help='Decoder max active states'),
        opt('beam', default=13.0, type=float,
            help='Decoding beam'),
        opt('lattice-beam', default=6.0, type=float,
            help='Lattice generation beam'))}


def decode(decoder, graph_dir):
        decoder.log.info('decoding and computing WER')

        # generate option string for decoding
        decode_opts = ' '.join('--{} {}'.format(n, str(o))
                               for n, o in decoder.decode_opts.iteritems())

        target = os.path.join(decoder.recipe_dir, 'decode')
        if not os.path.isdir(target):
            os.makedirs(target)

        decoder._run_command((
            'steps/decode.sh --nj {njobs} --cmd "{cmd}" '
            '--model {model} {decode_opts} {skip_scoring} '
            '--scoring-opts "{score_opts}" {graph} {data} {decode}'.format(
                njobs=decoder.njobs,
                cmd=utils.config.get('kaldi', 'decode-cmd'),
                # TODO .mdl or .alimdl ?
                model=os.path.join(decoder.am_dir, 'final.mdl'),
                decode_opts=decode_opts,
                skip_scoring=_score.skip_scoring(decoder.score_opts),
                score_opts=_score.format(
                    decoder.score_opts, decoder.mkgraph_opts),
                graph=graph_dir,
                data=os.path.join(decoder.recipe_dir, 'data', decoder.name),
                decode=target)))

        return target
