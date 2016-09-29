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


def _guess_type(value):
    if value.startswith('"'):
        return str
    elif '.' in value:
        return float
    else:
        return int


def _parse_options():
    """Return a dict[name] -> OptionEntry read from train_pnorm_fast.sh"""
    # read the help message from the script
    try:
        script = os.path.join('steps', 'nnet2', 'train_pnorm_fast.sh')
        path = os.path.join(
            utils.config.get('kaldi', 'kaldi-directory'), 'egs', 'wsj', 's5')

        # help message displayed on stderr with --help argument
        helpmsg = subprocess.Popen(
            os.path.join(path, script),
            stdout=subprocess.PIPE, cwd=path).communicate()[0]
    except OSError:
        raise RuntimeError(
            'No such file "{}" in directory {}'.format(script, path))

    # parse each option in a list
    exclude = ['mix-up', 'stage']
    started = False
    options = []
    for line in helpmsg.split('\n')[:-2]:
        if line.startswith('Main options'):
            started = True
            continue
        if started:
            m = re.match(r'^\s+--([\w\-?]+)\s+<.+\|(.+)>\s+\#\s+(.+)$', line)
            # new option
            if m and m.group(1) not in exclude:
                options.append(list(m.group(1, 2, 3)))
            # continuation of the comment
            elif line.strip().startswith('#'):
                options[-1][-1] += ' ' + ' '.join(line.split('#')[1:])

    # build a dict of OptionEntry
    return {o[0]: OptionEntry(help=o[2], default=o[1], type=_guess_type(o[1]))
            for o in options}


class NeuralNetwork(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/nnet2/train_pnorm_fast.sh

    Training is done on an abkhazia corpus, from previously computed
    language and acoustic models.

    Secondary options are not forwarded from Kaldi to Abkhazia (all
    the options not described in the script's help message)

    """
    model_type = 'nnet'

    options = _parse_options()

    def __init__(self, corpus, lm_dir, am_dir,
                 output_dir, log=utils.logger.null_logger):
        super(NeuralNetwork, self).__init__(
            corpus, lm_dir, am_dir, output_dir, log=log)

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
                '{data} {lang} {origin} {target}'.format(
                    data=self.data_dir,
                    lang=self.lm_dir,
                    origin=self.am_dir,
                    target=target))))

        self._run_am_command(command, target, message)
