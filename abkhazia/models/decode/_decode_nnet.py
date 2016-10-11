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
"""Wrapper on egs/wsj/s5/steps/decode_nnet.sh

Ignored options are: alignment_nnet, features_transform, model,
class_frame_counts, srcdir, ivector, blocksoftmax_dims,
blocksoftmax_active, stage, skp_scoring, num_threads

"""

import os
import abkhazia.utils as utils


def options():
    """Return default parameters for the decode script"""
    opt = utils.kaldi.options.make_option

    return {k: v for k, v in (
        opt('acwt', default=0.10, type=float,
            help=('Acoustic scale for decoding only really affects '
                  'pruning (scoring is on lattices)')),
        opt('beam', default=13.0, type=float,
            help='Decoding beam'),
        opt('lattice-beam', default=6.0, type=float,
            help='Lattice generation beam'),
        opt('min_active', default=200, type=int,
            help='Decoder min active states'),
        opt('max_active', default=7000, type=int,
            help='Decoder max active states'),
        opt('max_men', default=50000000, type=int, help='approx. limit to '
            'memory consumption during minimization in bytes'),
        opt('use-gpu', default=False, type=bool, help='yes|no|optionaly')
    )}


def decode(decoder, graph_dir):
    decoder.log.info('nnet decoding and computing WER')

    # generate option string for decoding
    decode_opts = ' '.join('--{} {}'.format(n, str(o))
                           for n, o in decoder.decode_opts.iteritems())

    # generate option string for scoring
    score_opts = ' '.join('--{} {}'.format(n, str(o))
                          for n, o in decoder.score_opts.iteritems())

    # generate option string for nnet-forward TODO access to
    # non-default options (as for scoring)
    nnet_forward_opts = "--no-softmax=true --prior-scale=1.0"

    target = os.path.join(decoder.recipe_dir, 'decode')
    if not os.path.isdir(target):
        os.makedirs(target)

    decoder._run_command((
        'steps/decode_nnet.sh --nj {njobs} --cmd "{cmd}" '
        '{decode_opts} --scoring-opts "{score_opts}" '
        '--nnet-forward-opts "{nnet_opts}" '
        '{graph} {data} {decode}'.format(
            njobs=decoder.njobs,
            cmd=utils.config.get('kaldi', 'decode-cmd'),
            decode_opts=decode_opts,
            score_opts=score_opts,
            nnet_opts=nnet_forward_opts,
            graph=graph_dir,
            data=os.path.join(decoder.recipe_dir, 'data', decoder.name),
            decode=target)))
