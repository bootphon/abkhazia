#!/usr/bin/env python

import os

import abkhazia.utils as utils
from abkhazia.corpus import Corpus
from abkhazia.models.align import Align
from abkhazia.models.language_model import read_int2phone


def export_phones_and_words(self, int2phones, ali, post):
    """Add word boundaries to the result of _export_phones(...)"""
    self.log = utils.logger.get_log(os.devnull, verbose=True)

    # phone level alignment
    phones = self._export_phones(int2phone, ali, post)

    # text[utt_id] = list of words
    text = {k: v.strip().split()
            for k, v in self.corpus.text.iteritems()}

    # phonemized[utt_id] = list of phones (from text)
    phonemized = self.corpus.phonemize_text()

    # lexicon[word] = list of phones
    lexicon = {k: v.strip().split()
               for k, v in self.corpus.lexicon.iteritems()}

    final_alignment = []
    for utt_id, utt_align in self._read_utts(phones):
        # ignoring all silences, ensure the utterance text is
        # consistant with the alignment (at phone level). NOTE this is
        # only a security check
        gold = [p for p in phonemized[utt_id].split()
                if p not in self.corpus.silences]
        raw = [p for p in (u.split()[-1] for u in utt_align)
               if p not in self.corpus.silences]
        assert gold == raw, \
            'matching error in alignment:\n{}\n{}'.format(
                ' '.join(gold), ' '.join(raw))

        final_alignment.append(' '.join(text[utt_id]))

        # add word boundaries to the aligned phones
        idx = 0
        for word in text[utt_id]:
            # consume any silence before the word if it's not part of
            # the word itself
            while utt_align[idx] in self.corpus.silences:
                final_alignment.append(utt_align[idx])
                idx += 1

            # add word boundary on the word's first phone
            final_alignment.append(utt_align[idx] + ' ' + word)
            idx += 1

            # add the rest of the word
            offset = len(lexicon[word]) - 1
            final_alignment += utt_align[idx:idx+offset]
            idx += offset

    return final_alignment
        # for p in align:
        #     if p not in self.corpus.silences:
        #         g = gold.pop(0)
        #         while g in self.corpus.silences:
        #             g = gold.pop(0)
        #         assert p == g, '{} {}'.format(p, g)


        # n = max(len(gold), len(align))
        # # Expand the list up to n empty elements
        # for _ in range(len(gold), n):
        #     gold.append('')
        # for _ in range(len(align), n):
        #     align.append('')

        # for g, a in zip(gold, align):
        #     print '{}\t{}'.format(g, a)

        # return

    #     idx = 0
    #     # for each word in transcription, parse it's aligned
    #     # phones and add the word after the first phone belonging
    #     # to that word.
    #     for word in text[utt_id]:
    #         try:
    #             wlen = len(lexicon[word])
    #         except KeyError:  # the word isn't in lexicon
    #             self.log.warning(
    #                 'ignoring out of lexicon word: %s', word)

    #         # from idx, we eat wlen phones (+ any silence phone)
    #         begin = True
    #         while wlen > 0:
    #             aligned = utt_align[idx]
    #             if aligned.split()[-1] in self.corpus.silences:
    #                 words.append('{}'.format(aligned))
    #             else:
    #                 words.append('{} {}'.format(
    #                     aligned, word if begin else ''))
    #                 wlen -= 1
    #                 begin = False
    #             idx += 1
    # return words


root_dir = ('/home/mathieu/lscp/dev/abkhazia/egs/'
            'align_childes_brent_1percent/split/train')
corpus = Corpus.load(os.path.join(root_dir, 'data'))
output_dir = os.path.dirname(__file__)

aligner = Align(corpus, output_dir)
aligner.feat_dir = os.path.join(root_dir, 'features')
aligner.lm_dir = os.path.join(root_dir, 'language')
aligner.am_dir = os.path.join(root_dir, 'acoustic')
aligner.recipe_dir = os.path.join(root_dir, 'align/recipe')
aligner.delete_recipe = False

int2phone = read_int2phone(aligner.lm_dir)
ali = aligner._read_result_utts('ali')

with open('./aligned.txt', 'w') as fout:
    fout.write('\n'.join(
        export_phones_and_words(aligner, int2phone, ali, None)))
