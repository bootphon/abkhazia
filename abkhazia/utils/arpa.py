# Copyright Maarten van Gompel, ILK, Universiteit van Tilburg
# Copyright 2015, 2016 Stefan Fischer
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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Python interface to ngrams language models in ARPA format

This class originates from the pynlpl library (GPL, ARPA loader) and
the python-arpa library (MIT, ARPA writer). See
https://github.com/proycon/pynlpl and
https://github.com/sfischer13/python-arpa.

"""

import os
import re
import utils  # this is abkhazia.utils


class ARPALanguageModel(object):
    def __init__(self, ngrams):
        """Build a LM from raw data

        ngrams is a dict of dicts, each inner dict corresponds to ngram
        of a given order: ngrams[1] and ngrams[2] are unigrams and
        bigrams respectively. ngrams[n] itself is a dict[(word_1, ...,
        word_n)] -> (probability, backoff)

        """
        self.order = len(ngrams)
        self.ngrams = ngrams

    @classmethod
    def load(cls, path):
        """Load an ARPA language model from the file `path`"""
        assert os.path.isfile(path)

        data = {}
        order = None
        for line in (l.strip() for l in utils.open_utf8(path, 'r') if l):
            if line.startswith('\\data\\'):
                order = 0
            elif line.startswith('\\end\\'):
                break
            elif line.startswith('\\') and line.endswith(':'):
                order = int(re.search('[0-9]+', line).group(0))
                if order not in data:
                    data[order] = {}
            elif line:
                if order == 0:  # still in \data\ section
                    pass
                elif order > 0:
                    line = line.split('\t')
                    prob = float(line[0])
                    ngram = tuple(line[1].split())
                    backoff = None if len(line) <= 2 else float(line[2])
                    data[order][ngram] = (prob, backoff)
                else:
                    raise IOError(
                        'unable to parse ARPA file line: {}'.format(line))
        return cls(data)

    def save(self, path):
        """Save a language model to `path` in the ARPA format

        Do not write empty ngrams to the `path`

        """
        with utils.open_utf8(path, 'w') as fp:
            # write header
            fp.write('\n\\data\\\n')
            for order in range(1, self.order+1):
                size = len(self.ngrams[order])
                if size:
                    fp.write('ngram {}={}\n'.format(order, size))
            fp.write('\n')

            # write ngrams
            for order in range(1, self.order+1):
                if len(self.ngrams[order]):
                    fp.write('\\{}-grams:\n'.format(order))
                    for k, v in sorted(self.ngrams[order].items()):
                        ngram = ' '.join(k)
                        if v[1] is None:  # no backoff
                            fp.write('{}\t{}\n'.format(v[0], ngram))
                        else:
                            fp.write('{}\t{}\t{}\n'.format(v[0], ngram, v[1]))
                    fp.write('\n')
            fp.write('\\end\\\n')

    def prune_vocabulary(self, words):
        """Remove any ngram entry containing a word not in `words`"""
        for ngram in self.ngrams.itervalues():
            for entry in ngram.keys():
                if not all(word in words for word in entry):
                    del ngram[entry]
