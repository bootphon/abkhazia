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
"""Training neural network acoustic models with pnorm nonlinearities"""

import os
import re
import subprocess

import abkhazia.utils as utils
from abkhazia.utils.kaldi.options import OptionEntry
from abkhazia.models.acoustic.abstract_acoustic_model import (
    AbstractAcousticModel)


# def _guess_type(value):
#     if value.startswith('"'):
#         return str
#     elif '.' in value:
#         return float
#     else:
#         return int


# def _parse_options():
#     """Return a dict[name] -> OptionEntry read from train_pnorm_fast.sh"""
#     # read the help message from the script
#     try:
#         script = os.path.join('steps', 'nnet2', 'train_pnorm_fast.sh')
#         path = os.path.join(
#             utils.config.get('kaldi', 'kaldi-directory'), 'egs', 'wsj', 's5')

#         # help message displayed on stderr with --help argument
#         helpmsg = subprocess.Popen(
#             os.path.join(path, script),
#             stdout=subprocess.PIPE, cwd=path).communicate()[0]
#     except OSError:
#         raise RuntimeError(
#             'No such file "{}" in directory {}'.format(script, path))

#     # parse each option in a list
#     exclude = ['mix-up', 'stage']
#     started = False
#     options = []
#     for line in helpmsg.split('\n')[:-2]:
#         if line.startswith('Main options'):
#             started = True
#             continue
#         if started:
#             m = re.match(r'^\s+--([\w\-?]+)\s+<.+\|(.+)>\s+\#\s+(.+)$', line)
#             # new option
#             if m and m.group(1) not in exclude:
#                 options.append(list(m.group(1, 2, 3)))
#             # continuation of the comment
#             elif line.strip().startswith('#'):
#                 options[-1][-1] += ' ' + ' '.join(line.split('#')[1:])

#     # build a dict of OptionEntry
#     return {o[0]: OptionEntry(help=o[2], default=o[1], type=_guess_type(o[1]))
#             for o in options}


class NeuralNetwork(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/nnet2/train_pnorm_fast.sh

    Training is done on an abkhazia corpus, from previously computed
    language and acoustic models.

    The following options are not forwarded from Kaldi to Abkhazia:
    get_egs_stage, online_ivector_dir, stage, cleanup, egs_dir,
    lda_opts, lda_dim, egs_opts, transform_dir, cmvn_opts, feat_type,
    prior_subset_size

    """
    model_type = 'nnet'

    # options = _parse_options()
    options = {k: v for k, v in (
        utils.kaldi.options.make_option(
            'num-epochs', default=15, type=int,
            help=('Number of epochs during which we reduce the learning rate; '
                  'number of iterations is worked out from this')),
        utils.kaldi.options.make_option(
            'num-epochs-extra', default=5, type=int,
            help='Number of epochs after we stop reducing the learning rate'),
        utils.kaldi.options.make_option(
            'num-iters-final', default=20, type=int,
            help=('Maximum number of final iterations to give to the '
                  'optimization over the validation set (maximum)')),
        utils.kaldi.options.make_option(
            'initial-learning-rate', default=0.04, type=float, help=''),
        utils.kaldi.options.make_option(
            'final-learning-rate', default=0.004, type=float, help=''),
        utils.kaldi.options.make_option(
            'bias-stddev', default=0.5, type=float, help=''),
        utils.kaldi.options.make_option(
            'pnorm-input-dim', default=3000, type=int, help=''),
        utils.kaldi.options.make_option(
            'pnorm-output-dim', default=300, type=int, help=''),
        utils.kaldi.options.make_option(
            'p', default=2, type=float, help='p in p-norm'),
        utils.kaldi.options.make_option(
            'presoftmax-prior-scale-power', default=-0.25, type=float,
            help=('use the specified power value on the priors (inverse '
                  'priors) to scale the pre-softmax outputs')),
        utils.kaldi.options.make_option(
            'minibatch-size', default=128, type=int,
            help='''by default use a smallish minibatch size for neural net
            training; this controls instability which would otherwise
            be a problem with multi-threaded update'''),
        utils.kaldi.options.make_option(
            'samples-per-iter', default=200000, type=int,
            help='each iteration of training, see this many samples per job'),
        utils.kaldi.options.make_option(
            'num-jobs-nnet', default=16, type=int,
            help='Number of neural net jobs to run in parallel'),
        utils.kaldi.options.make_option(
            'shuffle-buffer-size', default=500, type=int,
            help='''
            This "buffer_size" variable controls randomization of the samples
            on each iter. You could set it to 0 or to a large value
            for complete randomization, but this would both consume
            memory and cause spikes in disk I/O. Smaller is easier on
            disk and memory but less random. It's not a huge deal
            though, as samples are anyway randomized right at the
            start. (the point of this is to get data in different
            minibatches on different iterations, since in the
            preconditioning method, 2 samples in the same minibatch
            can affect each others' gradients.'''),
        utils.kaldi.options.make_option(
            'add-layers-period', default=2, type=int,
            help='add new layers every <int> iterations'),
        utils.kaldi.options.make_option(
            'num-hidden-layers', default=3, type=int, help=''),
        utils.kaldi.options.make_option(
            'io-opts', default='"-tc 5"', type=str, help=(
                'for jobs with a lot of I/O, limits the number '
                'running at one time')),
        utils.kaldi.options.make_option(
            'splice-width', default=4, type=int,
            help='meaning +- <int> frames on each side for second LDA'),
        utils.kaldi.options.make_option(
            'randprune', default=4.0, type=float,
            help='speeds up LDA'),
        utils.kaldi.options.make_option(
            'alpha', default=4.0, type=float,
            help='relates to preconditioning'),
        utils.kaldi.options.make_option(
            'target-multiplier', default=0, type=float,
            help='Set this to e.g. 1.0 to enable perturbed training'),
        utils.kaldi.options.make_option(
            'mix-up', default=0, type=int, help=(
                'Number of components to mix up to (should be > #tree leaves, '
                'if specified)')),
        utils.kaldi.options.make_option(
            'combine-num-threads', default=8, type=int,
            help='number of threads for the "combine" stage'),
        )}

    def __init__(self, corpus, lm_dir, feats_dir, am_dir,
                 output_dir, log=utils.logger.null_logger):
        super(NeuralNetwork, self).__init__(
            corpus, lm_dir, feats_dir, output_dir, log=log)

        self.am_dir = os.path.abspath(am_dir)
        utils.check_directory(
            self.am_dir, ['tree', 'final.mdl', 'ali.1.gz'])

    def run(self):
        self._train_pnorm_fast()

    def _train_pnorm_fast(self):
        message = 'training neural network'
        target = os.path.join(self.recipe_dir, 'exp', self.model_type)

        command = (
            ' '.join((
                'steps/nnet2/train_pnorm_fast.sh --cmd "{}"'.format(
                    utils.config.get('kaldi', 'train-cmd')),
                ' '.join('--{} {}'.format(
                    k, v.value) for k, v in self.options.iteritems()),
                ('--num-threads {0} '
                 # '--parallel-opts "--num-threads {0}"')
                 '--parallel-opts ""')
                .format(self.njobs),
                # '--combine-parallel-opts "--num-threads {}"'.format(
                #     self.options['combine-num-threads'].value),
                '--combine-parallel-opts ""',
                '{data} {lang} {origin} {target}'.format(
                    data=self.data_dir,
                    lang=self.lm_dir,
                    origin=self.am_dir,
                    target=target))))

        self._run_am_command(command, target, message)
