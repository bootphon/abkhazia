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
"""Wrapper on egs/wsj/s5/steps/decode_fmllr.sh

Ignored options are: alignment_model, adapt_model, final_model, stage,
num-threads, skip_scoring, max_fmllr_jobs

"""

import os
import abkhazia.utils as utils


def options():
    """Return default parameters for the decode script"""
    opt = utils.kaldi.options.make_option

    return {k: v for k, v in (
        opt('acwt', default=0.083333, type=float,
            help=('Acoustic weight used in getting fMLLR transforms, and also '
                  'in lattice generation')),
        opt('max-active', default=7000, type=int,
            help='Decoder max active states'),
        opt('beam', default=13.0, type=float,
            help='Decoding beam'),
        opt('lattice-beam', default=6.0, type=float,
            help='Lattice generation beam'),
        opt('first-beam', default=10.0, type=float,
            help='Beam used in initial, speaker indep. pass'),
        opt('first-max-active', default=2000, type=int,
            help='max-active used in initial pass'),
        opt('silence-weight', default=0.01, type=float,
            help='Posterior silence weight'),
        opt('fmllr-update-type', default='full', type=str,
            help='Update type for fMLLR (full|diag|offset|none)'))}


def decode(decoder, graph_dir):
    decoder.log.info('fmllr decoding and computing WER')

    # generate option string for decoding
    decode_opts = ' '.join('--{} {}'.format(n, str(o))
                           for n, o in decoder.decode_opts.iteritems())

    # generate option string for scoring
    score_opts = ' '.join('--{} {}'.format(n, str(o))
                          for n, o in decoder.score_opts.iteritems())
    # add the reverse flag if enabled in the mkgraph options
    if decoder.mkgraph_opts['reverse'].value:
        score_opts += ' --reverse true'

    # decode_fmllr.sh must be run from a subdirectory of the input
    # acoustic model directory (here decoder.am_dir). So we do: create
    # a subdir in am_dir as a symlink to the target recipe_dir, run
    # the script in it, and finally delete the symlink. Moreover the
    # script make a speaker independant decoding so we use the tweak
    # again for si.

    target_sa = os.path.join(decoder.recipe_dir, 'decode')
    if not os.path.isdir(target_sa):
        os.makedirs(target_sa)
    tempdir_sa = os.path.join(decoder.am_dir, 'decode_fmllr')
    os.symlink(target_sa, tempdir_sa)

    target_si = os.path.join(decoder.recipe_dir, 'decode.si')
    if not os.path.isdir(target_si):
        os.makedirs(target_si)
    tempdir_si = os.path.join(decoder.am_dir, 'decode_fmllr.si')
    os.symlink(target_si, tempdir_si)

    decoder._run_command((
        'steps/decode_fmllr.sh --nj {njobs} --cmd "{cmd}" '
        '{decode_opts} --scoring-opts "{score_opts}" '
        '{graph} {data} {decode}'.format(
            njobs=decoder.njobs,
            cmd=utils.config.get('kaldi', 'decode-cmd'),
            decode_opts=decode_opts,
            score_opts=score_opts,
            graph=graph_dir,
            data=os.path.join(decoder.recipe_dir, 'data', decoder.name),
            decode=tempdir_sa)))

    # remove the two symlinks we created in input am_dir
    utils.remove(tempdir_si)
    utils.remove(tempdir_sa)
