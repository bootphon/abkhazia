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
"""Training triphone speaker adapted acoustic models

Must be trained on top of a triphon speaker independant acoustic model
(see the Triphone class)

"""

import os

import abkhazia.utils as utils
from abkhazia.models.acoustic.abstract_acoustic_model import (
    AbstractAcousticModel)


class TriphoneSpeakerAdaptive(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/{align_fmllr, train_sat}.sh

    The parameter `tri-dir` is the path to the computed triphone
    speaker independent acoustic model. It must contains the files
    'ali.1.gz' and 'final.mdl', else an OSError is raised.

    Other parameters are the same as in AbstractAcousticModel.

    The following options are not forwarded from Kaldi to Abkhazia:
    train_tree=true, tree_stats_opts, context_opts, power,
    cluster_thresh, cluster_phones_opts, phone_map,
    compile_questions_opts.

    """
    model_type = 'tri-sa'

    options = {k: v for k, v in (
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
            'beam', default=10, type=int,
            help='Decoding beam used in alignment'),
        utils.kaldi.options.make_option(
            'retry-beam', default=40, type=int,
            help='Decoding beam for second try at alignment'),
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
            'fmllr-update-type', default='full', type=str,
            help='Update type for FMLLR (full|diag|offset|none)'),
        utils.kaldi.options.make_option(
            'realign-iterations', type=list, default=[10, 20, 30],
            help='Iterations on which to align features on the model'),
        utils.kaldi.options.make_option(
            'fmllr-iterations', type=list, default=[2, 4, 6, 12],
            help='Iterations on which to align features on the model'),
        utils.kaldi.options.make_option(
            'num-iterations', default=35, type=int,
            help='Number of iterations for training'),
        utils.kaldi.options.make_option(
            'max-iteration-increase', default=25, type=int,
            help='Last iteration to increase number of Gaussians on'),
        utils.kaldi.options.make_option(
            'silence-weight', default=0.0, type=float,
            help='Weight on silence in fMLLR estimation'),
        utils.kaldi.options.make_option(
            'num-leaves', default=2500, type=int,
            help='Maximum number of leaves to be used in tree-buliding'),
        utils.kaldi.options.make_option(
            'total-gaussians', default=15000, type=int,
            help='Target number of Gaussians at the end of training'),
    )}

    def __init__(self, corpus, lm_dir, feats_dir, tri_dir,
                 output_dir, log=utils.logger.null_logger):
        super(TriphoneSpeakerAdaptive, self).__init__(
            corpus, lm_dir, feats_dir, output_dir, log=log)

        self.tri_dir = os.path.abspath(tri_dir)
        utils.check_directory(
            self.tri_dir, ['final.mdl', 'ali.1.gz'])

    def run(self):
        align_dir = os.path.join(self.recipe_dir, 'exp', 'tri_ali_fmllr')
        self._align_fmllr(align_dir)
        self._train_sat(align_dir)

    def _align_fmllr(self, align_dir):
        """Wrapper on steps/align_fmllr.sh

        Computes training alignments; assumes features are (LDA+MLLT
        or delta+delta-delta) + fMLLR (probably with SAT models). It
        first computes an alignment with the final.alimdl (or the
        final.mdl if final.alimdl is not present), then does 2
        iterations of fMLLR estimation.

        """
        message = 'forced-aligning triphone model'

        command = (
            'steps/align_fmllr.sh --nj {njobs} --cmd "{cmd}" '
            '--scale-opts "--transition-scale={transition} '
            '--acoustic-scale={acoustic} --self-loop-scale={selfloop}" '
            '--beam {beam} --retry-beam {retrybeam} '
            '--careful {careful} --boost-silence {boost} '
            '--fmllr-update-type {fmllr} '
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
                fmllr=self._opt('fmllr-update-type'),
                data=self.data_dir,
                lang=self.lm_dir,
                origin=self.tri_dir,
                target=align_dir))
        self._run_am_command(command, align_dir, message)

    def _train_sat(self, ali_dir):
        """Wrapper on steps/train_sat.shallow

        This does Speaker Adapted Training (SAT), i.e. train on
        fMLLR-adapted features.  It can be done on top of either
        LDA+MLLT, or delta and delta-delta features.  If there are no
        transforms supplied in the alignment directory, it will
        estimate transforms itself before building the tree (and in
        any case, it estimates transforms a number of times during
        training).

        """
        message = 'training speaker-adaptive triphone model'
        target = os.path.join(self.recipe_dir, 'exp', self.model_type)

        if not os.path.isdir(ali_dir):
            raise RuntimeError(
                'unexisting directory: {}, please provide alignments '
                'using align_fmllr'.format(ali_dir))

        command = (
            'steps/train_sat.sh --cmd "{cmd}" '
            '--scale-opts "--transition-scale={transition} '
            '--acoustic-scale={acoustic} --self-loop-scale={selfloop}" '
            '--realign-iters {realign} --num-iters {niters} '
            '--careful {careful} --boost-silence {boost} '
            '--fmllr-update-type {fmllr} --silence-weight {silence} '
            '--fmllr-iters {fmllriters} '
            '--max-iter-inc {maxiter} --beam {beam} --retry-beam {retrybeam} '
            '{numleaves} {totgauss} {data} {lang} {origin} {target}'
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
                fmllr=self._opt('fmllr-update-type'),
                silence=self._opt('silence-weight'),
                fmllriters=self._opt('fmllr-iterations'),
                data=self.data_dir,
                lang=self.lm_dir,
                origin=ali_dir,
                target=target))
        self._run_am_command(command, target, message)
