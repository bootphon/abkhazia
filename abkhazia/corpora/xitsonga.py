# coding: utf-8

"""Data preparation for the Xitsonga corpus"""

from corpus_preparator import AbstractPreparator


# IPA transcriptions for all phones
XITSONGA_PHONES = [
    ('n\'', u'ɳ'),
    ('K', u'ɬ'),
    ('tl_>', u'tl\''),
    ('tl_h', u'tlʰ'),
    ('d', u'd'),
    ('E', u'Ɛ'),
    ('a', u'a'),
    ('gh\\', u'gɦ'),
    ('j', u'j'),
    ('tj_h', u'tjʰ'),
    ('u', u'u'),
    ('d_0Z', u'ʤ'),
    ('k', u'k'),
    ('g', u'g'),
    ('pj_h', u'pjʰ'),
    ('dz`h\\', u'dʐɦ'),
    ('dZh\\', u'ʤh'),
    ('J', u'ɲ'),
    ('n_h', u'nɦ'),
    ('tj', u'tj'),
    ('bj', u'bj'),
    ('v', u'v'),
    ('B', u'β'),
    ('s', u's'),
    ('S', u'ʃ'),
    ('k_h', u'kʰ'),
    ('pj_>', u'pj\''),
    ('tS_>', u'ts\ʼ'),
    ('tS_h', u'tsʰ'),
    ('b', u'b'),
    ('z', u'z'),
    ('dz`', u'dʐ'),
    ('b_<', u'ɓ'),
    ('w', u'w'),
    ('r', u'r'),
    ('t_h', u'tʰ'),
    ('rh\\', u'rɦ'),
    ('m_h', u'mɦ'),
    ('s`', u'ʂ'),
    ('p_h', u'pʰ'),
    ('f', u'f'),
    ('i', u'i'),
    ('dh\\', u'dɦ'),
    ('h\\', u'ɦ'),
    ('O', u'ɔ'),
    ('n', u'n'),
    ('N', u'ŋ'),
    ('dK\\', u'dɮ'),
    ('dK', u'dɬ'),
    ('!\\', u'!'),
    ('m', u'm'),
    ('dj', u'dj'),
    ('l', u'l'),
    ('p', u'p'),
    ('t_>', u't\''),
]


class XitsongaPreparator(AbstractPreparator):
    """Convert the Xitsonga corpus to the abkhazia format

    This class specializes the AbstractPreparator for the Xitsonga
    corpus and implements the steps 2 to 7.

    """

    def _2_link_wavs(self):
        wav_src = os.path.join(self.input_dir, 'audio')

        input_wav = list_wavs(wav_src)
        if os.path.isdir(wav_dir):
            shutil.rmtree(wav_dir)
            os.makedirs(wav_dir)
            for wav_file in input_wav:
                bname = os.path.basename(wav_file)
                #rename all wav files so that wav files start by speaker_ID
                short_bname = bname.replace('nchlt_tso_', '')
                path_shortname = os.path.join(wav_dir, short_bname)
                os.symlink(wav_file, path_shortname)
        print ('finished linking wav files')


    def _3_make_segment(self):
        output_file = os.path.join(data_dir, 'segments.txt')
        wav_dir = os.path.join(data_dir, 'wavs')
        make_segment(wav_dir, output_file)

    def _4_make_speaker(self):
        output_file = os.path.join(data_dir, 'utt2spk.txt')
        wav_dir = os.path.join(data_dir, 'wavs')
        make_speaker(wav_dir, output_file)

    def _5_make_transcription(self):
        segment_file = os.path.join(data_dir, 'segments.txt')
        trs_dir = os.path.join(raw_Xitsonga_path, 'transcriptions')
        output_file = os.path.join(data_dir, 'text.txt')
        make_transcription(segment_file, trs_dir, output_file)

    def _6_make_lexicon(self):
        outfile_lexicon = os.path.join(data_dir, 'lexicon.txt')
        outfile_temp = os.path.join(log_dir, 'temp.txt')
        mlf_dir = os.path.join(raw_Xitsonga_path, 'mlfs_tso')
        make_lexicon(outfile_lexicon, outfile_temp, mlf_dir)

    def _7_make_phones(self):
        phones = {}
        for phone, ipa in Xitsonga_phones:
            phones[phone] = ipa
        silences = [u"NSN"]  # SPN and SIL will be added automatically
        variants = []  # could use lexical stress variants...
        make_phones(phones, data_dir, silences, variants)
        print("Created phones.txt, silences.txt, variants.txt")
