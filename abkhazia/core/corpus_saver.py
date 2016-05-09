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
"""Provides the CorpusSaver class"""

import os
import abkhazia.utils as utils


class CorpusSaver(object):
    """Save a corpus to a directory"""
    @classmethod
    def save(cls, corpus, path, copy_wavs=False):
        """Save the `corpus` to the directory `path`

        `path` is assumed to be a non existing directory.

        `corpus` is a instance of Corpus

        If `copy_wavs` if True, force a file copy, else use symlinks.

        """
        def _path(f):
            return os.path.join(path, f)

        os.makedirs(path)
        cls.save_wavs(corpus, _path('wavs'))
        cls.save_lexicon(corpus, _path('lexicon.txt'))
        cls.save_segments(corpus, _path('segments.txt'))
        cls.save_text(corpus, _path('text.txt'))
        cls.save_phones(corpus, _path('phones.txt'))
        cls.save_silences(corpus, _path('silences.txt'))
        cls.save_utt2spk(corpus, _path('utt2spk.txt'))
        cls.save_variants(corpus, _path('variants.txt'))

    @staticmethod
    def save_wavs(corpus, path, copy_wavs=False):
        os.makedirs(path)

        for wav in (os.path.realpath(w) for w in corpus.wavs.itervalues()):
            target = os.path.join(path, os.path.basename(wav))
            # if copy_wavs is True:
            #     shutil.copy(wav, target)
            # else:
            os.symlink(wav, target)

    @staticmethod
    def save_lexicon(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in corpus.lexicon.iteritems():
                out.write('{} {}\n'.format(k, v))

    @staticmethod
    def save_segments(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in corpus.segments.iteritems():
                # different case with/without timestamps
                v = (v[0] if v[1] is None and v[2] is None
                     else '{} {} {}'.format(v[0], v[1], v[2]))
                out.write('{} {}\n'.format(k, v))

    @staticmethod
    def save_text(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in corpus.text.iteritems():
                out.write('{} {}\n'.format(k, v))

    @staticmethod
    def save_phones(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for k, v in corpus.phones.iteritems():
                out.write(u'{} {}\n'.format(k, v))

    @staticmethod
    def save_silences(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for s in corpus.silences:
                out.write('{}\n'.format(s))

    @staticmethod
    def save_utt2spk(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for utt, spk in corpus.utt2spk.iteritems():
                out.write('{} {}\n'.format(utt, spk))

    @staticmethod
    def save_variants(corpus, path):
        with utils.open_utf8(path, 'w') as out:
            for v in corpus.variants:
                out.write('{}\n'.format(v))
