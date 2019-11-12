# Copyright 2016-2018 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Training monophone acoustic models"""

import gzip
import os

import abkhazia.utils as utils
import abkhazia.features as features
from abkhazia.acoustic.abstract_acoustic_model import (
    AbstractAcousticModel)
from abkhazia.align.align import convert_alignment_to_kaldi_format
import abkhazia.kaldi as kaldi


class Monophone(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/train_mono.sh

    Training is done on an abkhazia corpus, from computed features with cmvn.

    The following options are not forwarded from Kaldi to
    Abkhazia: power, cmvn_opts.

    """
    model_type = 'mono'

    options = {k: v for k, v in (
        kaldi.options.make_option(
            'transition-scale', default=1.0, type=float,
            help='Transition-probability scale (relative to acoustics)'),
        kaldi.options.make_option(
            'self-loop-scale', default=0.1, type=float,
            help=('Scale of self-loop versus non-self-loop log probs '
                  '(relative to acoustics)')),
        kaldi.options.make_option(
            'acoustic-scale', default=0.1, type=float,
            help='Scaling factor for acoustic likelihoods'),
        kaldi.options.make_option(
            'num-iterations', default=40, type=int,
            help='Number of iterations for training'),
        kaldi.options.make_option(
            'max-iteration-increase', default=30, type=int,
            help='Last iteration to increase number of Gaussians on'),
        kaldi.options.make_option(
            'total-gaussians', default=1000, type=int,
            help='Target number of Gaussians at the end of training'),
        kaldi.options.make_option(
            'careful', default=False, type=bool,
            help=('If true, do careful alignment, which is better at '
                  'detecting alignment failure (involves loop to start '
                  'of decoding graph)')),
        kaldi.options.make_option(
            'boost-silence', default=1.0, type=float,
            help=('Factor by which to boost silence likelihoods '
                  'in alignment')),
        kaldi.options.make_option(
            'realign-iterations', type=list,
            default=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12,
                     14, 16, 18, 20, 23, 26, 29, 32, 35, 38],
            help='Iterations on which to align features on the model'))}

    def __init__(self, corpus, feats_dir, output_dir, lang_args,
                 log=utils.logger.null_logger()):
        super(Monophone, self).__init__(
            corpus, feats_dir, output_dir, lang_args, log=log)

    def check_parameters(self):
        super(Monophone, self).check_parameters()

        # ensure cmvn are computed for the features
        features.Features.check_features(self.input_dir, cmvn=True)

    def run(self):
        self._train_mono()

    def _train_mono(self):
        # Flat start and monophone training, with delta-delta features.
        # This script applies cepstral mean normalization (per speaker).
        message = 'training monophone model'
        target = os.path.join(self.recipe_dir, 'exp', self.model_type)
        command = (
            'steps/train_mono.sh --nj {njobs} --cmd "{cmd}" '
            '--scale-opts "--transition-scale={transition} '
            '--acoustic-scale={acoustic} --self-loop-scale={selfloop}" '
            '--num-iters {niters} --max-iter-inc {maxinc} --totgauss {ngauss} '
            '--careful {careful} --boost-silence {boost} '
            '--realign-iters {realign} {data} {lang} {target}'
            .format(
                njobs=self.njobs,
                cmd=utils.config.get('kaldi', 'train-cmd'),
                transition=self._opt('transition-scale'),
                acoustic=self._opt('acoustic-scale'),
                selfloop=self._opt('self-loop-scale'),
                niters=self._opt('num-iterations'),
                maxinc=self._opt('max-iteration-increase'),
                ngauss=self._opt('total-gaussians'),
                careful=self._opt('careful'),
                boost=self._opt('boost-silence'),
                realign=self._opt('realign-iterations'),
                data=self.data_dir,
                lang=self.lang_dir,
                target=target))
        self._run_am_command(command, target, message)


class MonophoneFromAlignment(Monophone):
    """Train a monophone model from a corpus with an existing alignment

    This recipe bypass the alignment iterations in the original recipe

    """
    def __init__(self, corpus, feats_dir, output_dir, lang_args,
                 alignment_file, log=utils.logger.null_logger()):
        super(MonophoneFromAlignment, self).__init__(
            corpus, feats_dir, output_dir, lang_args, log=log)

        self.alignment_file = alignment_file
        self.options['realign-iterations'] = 0

    def create(self):
        super(MonophoneFromAlignment, self).create()

        # convert alignment to Kaldi format. TODO be carefull here, we
        # use the default values for features, if using non-default
        # values for features frame width and spacing, this will not
        # work!
        self.log.info(
            'using existing alignment: {}, conversion to Kaldi format...'
            .format(self.alignment_file))

        ali = convert_alignment_to_kaldi_format(
            self.alignment_file,
            os.path.join(self.output_dir, 'lang'),
            self.lang_args['position_dependent_phones'],
            log=self.log)

        # split the data for njobs processing, this normally done in
        # the run() step but we need here to split the alignment
        # before calling the train_mono.sh script
        self._run_command(
            './utils/split_data.sh data/acoustic {}'.format(self.njobs))

        # build a dict utt -> split to split the alignement following
        # the data split distribution
        split_utt = {}
        for job in range(1, self.njobs + 1):
            utt2spk = os.path.join(
                self.recipe_dir, 'data', 'acoustic',
                'split{}'.format(self.njobs), '{}'.format(job), 'utt2spk')
            for line in open(utt2spk, 'r'):
                split_utt[line.split(' ')[0]] = job

        # split the alignment
        self.log.info('spliting alignment...')
        split_ali = {}
        for job in range(1, self.njobs + 1):
            split_ali[job] = []
        for utt, line in ali.items():
            try:
                job = split_utt[utt]
                split_ali[job].append(utt + ' ' + line.strip())
            except KeyError:
                pass  # the utterance is not in the data splits, ignore it

        # put the files as recipe/exp/mono/ali.JOB.gz
        exp_dir = os.path.join(self.recipe_dir, 'exp', 'mono')
        if not os.path.exists(exp_dir):
            os.makedirs(exp_dir)
        for job in range(1, self.njobs + 1):
            ali_file = os.path.join(exp_dir, 'ali.{}.gz'.format(job))
            self.log.info('writing {}'.format(ali_file))
            gzip.open(ali_file, 'w').write('\n'.join(split_ali[job]) + '\n')
