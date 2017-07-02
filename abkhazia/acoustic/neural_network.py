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
import pkg_resources

import abkhazia.utils as utils
from abkhazia.acoustic.abstract_acoustic_model import (
    AbstractAcousticModel)
import abkhazia.kaldi as kaldi


class NeuralNetwork(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/nnet2/train_pnorm_fast.sh

    Training is done on an abkhazia corpus, from a previously computed
    acoustic model.

    The following options are not forwarded from Kaldi to Abkhazia:
    get_egs_stage, online_ivector_dir, stage, cleanup, egs_dir,
    lda_opts, lda_dim, egs_opts, transfrm_dir, cmvn_opts, feat_type,
    prior_subset_size

    A single option from egs_opts is forwarded: num_utts_subset. This
    allows to train on very small corpora, as used in the tests...

    """
    model_type = 'nnet'

    options = {k: v for k, v in (
        kaldi.options.make_option(
            'num-epochs', default=15, type=int,
            help=('Number of epochs during which we reduce the learning rate; '
                  'number of iterations is worked out from this')),
        kaldi.options.make_option(
            'num-epochs-extra', default=5, type=int,
            help='Number of epochs after we stop reducing the learning rate'),
        kaldi.options.make_option(
            'num-iters-final', default=20, type=int,
            help=('Maximum number of final iterations to give to the '
                  'optimization over the validation set (maximum)')),

        # TODO have a help message for those arguments
        kaldi.options.make_option(
            'initial-learning-rate', default=0.04, type=float, help=''),
        kaldi.options.make_option(
            'final-learning-rate', default=0.004, type=float, help=''),
        kaldi.options.make_option(
            'bias-stddev', default=0.5, type=float, help=''),
        kaldi.options.make_option(
            'pnorm-input-dim', default=3000, type=int, help=''),
        kaldi.options.make_option(
            'pnorm-output-dim', default=300, type=int, help=''),

        kaldi.options.make_option(
            'p', default=2, type=float, help='p in p-norm'),
        kaldi.options.make_option(
            'presoftmax-prior-scale-power', default=-0.25, type=float,
            help=('use the specified power value on the priors (inverse '
                  'priors) to scale the pre-softmax outputs')),
        kaldi.options.make_option(
            'minibatch-size', default=128, type=int,
            help='''by default use a smallish minibatch size for neural net
            training; this controls instability which would otherwise
            be a problem with multi-threaded update'''),
        kaldi.options.make_option(
            'samples-per-iter', default=200000, type=int,
            help='each iteration of training, see this many samples per job'),
        kaldi.options.make_option(
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
        kaldi.options.make_option(
            'add-layers-period', default=2, type=int,
            help='add new layers every <int> iterations'),
        kaldi.options.make_option(
            'num-hidden-layers', default=3, type=int, help=''),

        kaldi.options.make_option(
            'splice-width', default=4, type=int,
            help='meaning +- <int> frames on each side for second LDA'),
        kaldi.options.make_option(
            'randprune', default=4.0, type=float,
            help='speeds up LDA'),
        kaldi.options.make_option(
            'alpha', default=4.0, type=float,
            help='relates to preconditioning'),
        kaldi.options.make_option(
            'target-multiplier', default=0, type=float,
            help='Set this to e.g. 1.0 to enable perturbed training'),
        kaldi.options.make_option(
            'mix-up', default=0, type=int, help=(
                'Number of components to mix up to (should be > #tree leaves, '
                'if specified)')),
        kaldi.options.make_option(
            'num-utts-subset', default=300, type=int, help='''
            number of utterances in validation and training
            subsets used for shrinkage and diagnostics.
            Should have 2*num-utt-subset <= corpus.nutts'''),

        kaldi.options.make_option(
            'max-high-io-jobs', default=-1, type=int,
            help=('limits the number of jobs with lots of I/O running '
                  'at one time, default is -1 (no limit). This value is '
                  'translated into the "-tc <int>" before to be passed to the '
                  'queuing system')),
        kaldi.options.make_option(
            'combine-num-threads', default=8, type=int,
            help='number of threads for the "combine" stage'),
        kaldi.options.make_option(
            'num-jobs-nnet', default=16, type=int,
            help=('Number of neural net jobs to run in parallel, '
                  'set this to 1 to run on GPU '
                  '(if Kaldi is compiled with CUDA support)')))}

    # njobs related options
    _njobs_options = [
        'max-high-io-jobs', 'combine-num-threads', 'num-jobs-nnet']

    # options forwarded to get_egs.sh
    _egs_options = ['num-utts-subset']

    def __init__(self, corpus, feats_dir, am_dir,
                 output_dir, lang_args, log=utils.logger.null_logger):
        super(NeuralNetwork, self).__init__(
            corpus, feats_dir, output_dir, lang_argslog=log)

        self.am_dir = os.path.abspath(am_dir)
        utils.check_directory(
            self.am_dir, ['tree', 'final.mdl', 'ali.1.gz'])

    def run(self):
        self._train_pnorm_fast()

    def _train_pnorm_fast(self):
        message = 'training neural network'
        target = os.path.join(self.recipe_dir, 'exp', self.model_type)

        # format the nnet parameters options except njobs relatedd
        # that need further preprocessing/formatting (see above)
        nnet_opts = ' '.join(
            '--{} {}'.format(k, v.value)
            for k, v in self.options.iteritems()
            if k not in self._njobs_options and k not in self._egs_options)

        # convert the max_high_io_jobs option to what kaldi expect...
        _maxiojobs = self.options['max-high-io-jobs'].value
        io_opt = '--io-opts "{}"'.format(
            '' if _maxiojobs <= 0 else '-tc {}'.format(_maxiojobs))

        num_threads_opt = (
            '--num-threads {0} --parallel-opts "--num-threads {0}"'
            .format(self.njobs))

        combine_opt = (
            '--combine-num-threads {0} '
            '--combine-parallel-opts "--num-threads {0}"'
            .format(self.options['combine-num-threads'].value))

        egs_opts = '--egs-opts "{}"'.format(
            ' '.join('--{} {}'.format(k, v.value)
                     for k, v in self.options.iteritems()
                     if k in self._egs_options))

        # feeding the --cmd option
        job_cmd = utils.config.get('kaldi', 'train-cmd')
        if 'queue' in job_cmd:
            job_cmd += ' --config {}'.format(
                pkg_resources.resource_filename(
                    pkg_resources.Requirement.parse('abkhazia'),
                    'abkhazia/share/queue.conf'))

        command = (
            ' '.join((
                'steps/nnet2/train_pnorm_fast.sh --cmd "{}"'.format(job_cmd),
                nnet_opts, io_opt, egs_opts, num_threads_opt, combine_opt,
                '{data} {lang} {origin} {target}'.format(
                    data=self.data_dir,
                    lang=self.lang_dir,
                    origin=self.am_dir,
                    target=target))))

        self._run_am_command(command, target, message)
