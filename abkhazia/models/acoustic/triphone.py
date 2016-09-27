# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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
"""Training triphone speaker independent acoustic models

Must be trained on top of a monophone acoustic model (see the
Monophone class)

"""

import os

import abkhazia.utils as utils
from abkhazia.models.acoustic.abstract_acoustic_model import (
    AbstractAcousticModel)


class Triphone(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/{align_si, train_deltas}.sh

    The parameter `mono-dir` is the path to the computed monophone
    acoustic model. It must contains the files 'tree', 'final.mdl' and
    'final.occs', else an OSError is raised.

    Other parameters are the same as in AbstractAcousticModel.

    The following options are not forwarded from Kaldi to Abkhazia:
    use_graphs, power, cluster_thresh, cmvn_opts, delta_opts,
    context_opts.

    """
    model_type = 'tri'

    def __init__(self, corpus, lm_dir, feats_dir, mono_dir,
                 output_dir, log=utils.logger.null_logger):
        super(Triphone, self).__init__(
            corpus, lm_dir, feats_dir, output_dir, log=log)

        self.mono_dir = os.path.abspath(mono_dir)
        utils.check_directory(
            self.mono_dir, ['tree', 'final.mdl', 'final.occs'])

        self.options = {k: v for k, v in (
            utils.kaldi.options.make_option(
                'transition-scale', default=1.0, type=float,
                help='Transition-probability scale (relative to acoustics)'),
            utils.kaldi.options.make_option(
                'self-loop-scale', default=0.1, type=float,
                help=('Scale of self-loop versus non-self-loop log probs '
                      '(relative to acoustics)')),
            utils.kaldi.options.make_option(
                'acoustic-scale', default=0.1, type=float,
                help='Scaling factor for acoustic likelihoods'),
            utils.kaldi.options.make_option(
                'num-iterations', default=35, type=int,
                help='Number of iterations for training'),
            utils.kaldi.options.make_option(
                'max-iteration-increase', default=25, type=int,
                help='Last iteration to increase number of Gaussians on'),
            utils.kaldi.options.make_option(
                'careful', default=False, type=bool,
                help=('If true, do careful alignment, which is better at '
                      'detecting alignment failure (involves loop to start '
                      'of decoding graph)')),
            utils.kaldi.options.make_option(
                'boost-silence', default=1.0, type=float,
                help=('Factor by which to boost silence likelihoods '
                      'in alignment')),
            utils.kaldi.options.make_option(
                'realign-iterations', type=list, default=[10, 20, 30],
                help='Iterations on which to align features on the model'),
            utils.kaldi.options.make_option(
                'beam', default=10, type=int,
                help='Decoding beam used in alignment'),
            utils.kaldi.options.make_option(
                'retry-beam', default=40, type=int,
                help='Decoding beam for second try at alignment'),
            utils.kaldi.options.make_option(
                'num-leaves', default=2500, type=int,
                help='Maximum number of leaves to be used in tree-buliding'),
            utils.kaldi.options.make_option(
                'total-gaussians', default=15000, type=int,
                help='Target number of Gaussians at the end of training'),
        )}

    def run(self):
        align_dir = os.path.join(self.recipe_dir, 'exp', 'mono_ali')
        self._align_si(align_dir)
        self._train_deltas(align_dir)

    def _align_si(self, output_dir):
        """Wrapper on steps/align_si.sh

        Computes training alignments using a model with delta or
        LDA+MLLT features

        The Kaldi pipeline is:
        * apply-cmvn on features in feats_dir
        * gmm-boost-silence on model in mono_dir
        * compile-train-graphs on model in mono_dir and LM in lm_dir
        * gmm-align-compiled on features, model and train graph

        """
        message = 'force-aligning monophone model'

        command = (
            'steps/align_si.sh --nj {njobs} --cmd "{cmd}" '
            '--scale-opts "--transition-scale={transition} '
            '--acoustic-scale={acoustic} --self-loop-scale={selfloop}" '
            '--beam {beam} --retry-beam {retrybeam} '
            '--careful {careful} --boost-silence {boost} '
            '{data} {lang} {origin} {target}'
            .format(
                njobs=self.njobs,
                cmd=utils.config.get('kaldi', 'train-cmd'),
                transition=self._opt('transition-scale'),
                acoustic=self._opt('acoustic-scale'),
                selfloop=self._opt('self-loop-scale'),
                beam=self._opt('beam'),
                retrybeam=self._opt('retry-beam'),
                careful=self._opt('careful'),
                boost=self._opt('boost-silence'),
                data=self.data_dir,
                lang=self.lm_dir,
                origin=self.mono_dir,
                target=output_dir))
        self._run_am_command(command, output_dir, message)

    def _train_deltas(self, ali_dir):
        message = 'training speaker-independant triphone model'
        target = os.path.join(self.recipe_dir, 'exp', self.model_type)

        if not os.path.isdir(ali_dir):
            raise RuntimeError(
                'unexisting directory: {}, please provide alignments '
                'using align_si'.format(ali_dir))

        command = (
            'steps/train_deltas.sh --cmd "{cmd}" '
            '--scale-opts "--transition-scale={transition} '
            '--acoustic-scale={acoustic} --self-loop-scale={selfloop}" '
            '--realign-iters {realign} --num-iters {niters} '
            '--max-iter-inc {maxiter} --beam {beam} --retry-beam {retrybeam} '
            '--careful {careful} --boost-silence {boost} '
            '{numleaves} {totgauss} {data} {lang} {origin} {target} '
            .format(
                cmd=utils.config.get('kaldi', 'train-cmd'),
                transition=self._opt('transition-scale'),
                acoustic=self._opt('acoustic-scale'),
                selfloop=self._opt('self-loop-scale'),
                beam=self._opt('beam'),
                retrybeam=self._opt('retry-beam'),
                careful=self._opt('careful'),
                boost=self._opt('boost-silence'),
                maxiter=self._opt('max-iteration-increase'),
                realign=self._opt('realign-iterations'),
                niters=self._opt('num-iterations'),
                numleaves=self._opt('num-leaves'),
                totgauss=self._opt('total-gaussians'),
                data=self.data_dir,
                lang=self.lm_dir,
                origin=ali_dir,
                target=target))
        self._run_am_command(command, target, message)
