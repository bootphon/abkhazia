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

Ignored options are: stage, iter, skip_scoring, feat_type,
online_ivector_dir

"""

import os
import abkhazia.utils as utils
import abkhazia.kaldi as kaldi
from abkhazia.decode import _score


def options():
    """Return default parameters for the decode script"""
    opt = kaldi.options.make_option

    return {k: v for k, v in (
        opt('acwt', default=0.10, type=float,
            help=('Acoustic scale for decoding used for adaptation '
                  'and beam pruning')),
        opt('beam', default=15.0, type=float,
            help='Decoding beam'),
        opt('lattice-beam', default=8.0, type=float,
            help='Lattice generation beam'),
        opt('min-active', default=200, type=int,
            help='Decoder min active states'),
        opt('max-active', default=7000, type=int,
            help='Decoder max active states'),
        opt('num-threads', default=1, type=int,
            help='number of threads per jobs for lattice generation'),
        opt('minimize', default=False, type=bool,
            help='If true, push and minimize after determinization'),
        opt('transform-dir', default='', type=str,
            help='''directory of previous decoding (speaker adaptive decoding,
            i.e. tri-sa model), with "trans.*" files in it''')
    )}


def decode(decoder, graph_dir):
    decoder.log.info('nnet decoding and computing WER')

    # generate option string for decoding
    decode_opts = ' '.join('--{} {}'.format(n, str(o))
                           for n, o in decoder.decode_opts.items()
                           if n != 'transform-dir')
    _k = decoder.decode_opts['transform-dir'].value
    if _k != '':
        decode_opts += ' --transform-dir {}'.format(_k)

    target = os.path.join(decoder.recipe_dir, 'decode')
    if not os.path.isdir(target):
        os.makedirs(target)

    # link requested files to decoder.recipe_dir. final.mdl is
    # mandatory (raise if not found), others are optional and Kaldi
    # will work without
    for linked in ('final.mdl', 'cmvn_opts', 'final.mat',
                   'splice_opts', 'delta_order', 'log'):
        src = os.path.join(decoder.am_dir, linked)
        if os.path.exists(src):
            os.symlink(src, os.path.join(decoder.recipe_dir, linked))
        elif linked == 'final.mdl':
            raise IOError('acoustic model file not found: {}'.format(src))
        else:
            decoder.log.info('optional file not here %s', src)

    # TODO train_pnorm_fast script outputs a lda.mat file, is it the
    # final.mat requested by decode.sh ? -> NO
    # src = os.path.join(decoder.am_dir, 'lda.mat')
    # if os.path.isfile(src):
    #     os.symlink(src, os.path.join(decoder.recipe_dir, 'final.mat'))

    decoder._run_command((
        'steps/nnet2/decode.sh --nj {njobs} --cmd "{cmd}" {decode_opts} '
        '--parallel-opts "{paral}" '
        '{skip_scoring} --scoring-opts "{score_opts}" '
        '{graph} {data} {decode}'.format(
            njobs=decoder.njobs,
            cmd=utils.config.get('kaldi', 'decode-cmd'),
            decode_opts=decode_opts,
            paral='--num-threads {}'.format(
                decoder.decode_opts['num-threads'].value),
            skip_scoring=_score.skip_scoring(decoder.score_opts),
            score_opts=_score.format(decoder.score_opts, decoder.mkgraph_opts),
            graph=graph_dir,
            data=os.path.join(decoder.recipe_dir, 'data', decoder.name),
            decode=target)))
