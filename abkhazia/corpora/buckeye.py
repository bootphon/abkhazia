# coding: utf-8

"""Data preparation for the revised Buckeye corpus (in the original format)"""

from corpus_preparator import AbstractPreparator
from corpus_utils import list_files_with_extension


def list_word_files(directory):
    """Return the list of word files in the directory"""
    list_files_with_extension(directory, 'word_new')


def list_txt_files(directory):
    """Return the list of txt files in the directory"""
    list_files_with_extension(directory, 'txt')



# IPA transcriptions for all phones in the Buckeye corpus. The
# following phones are never found in the transcriptions: set([u'own',
# u'ahn', u'ihn', u'ayn', u'NSN', u'eyn', u'oyn', u'ehn', u'iyn',
# u'B', u'E', u'uhn', u'aon', u'awn', u'uwn', u'aan', u'ern', u'aen'])
# Reason: we already collapsed them in the foldings_version
BUCKEYE_PHONES = [
    ('iy', u'iː'),
    ('ih', u'ɪ'),
    ('eh', u'ɛ'),
    ('ey', u'eɪ'),
    ('ae', u'æ'),
    ('aa', u'ɑː'),
    ('aw', u'aʊ'),
    ('ay', u'aɪ'),
    ('ah', u'ʌ'),
    ('ao', u'ɔː'),
    ('oy', u'ɔɪ'),
    ('ow', u'oʊ'),
    ('uh', u'ʊ'),
    ('uw', u'uː'),
    ('er', u'ɝ'),
    ('jh', u'ʤ'),
    ('ch', u'ʧ'),
    ('b', u'b'),
    ('d', u'd'),
    ('g', u'g'),
    ('p', u'p'),
    ('t', u't'),
    ('k', u'k'),
    ('dx', u'ɾ'),
    ('s', u's'),
    ('sh', u'ʃ'),
    ('z', u'z'),
    ('zh', u'ʒ'),
    ('f', u'f'),
    ('th', u'θ'),
    ('v', u'v'),
    ('dh', u'ð'),
    ('m', u'm'),
    ('n', u'n'),
    ('ng', u'ŋ'),
    ('em', u'm\u0329'),
    ('nx', u'ɾ\u0303'),
    ('en', u'n\u0329'),
    ('eng', u'ŋ\u0329'),
    ('l', u'l'),
    ('r', u'r'),
    ('w', u'w'),
    ('y', u'j'),
    ('hh', u'h'),
    ('el', u'l\u0329'),
    ('tq', u'ʔ'),
    ('B', u'B'),
    ('E', u'E'),
    ('ahn', u'ʌ\u0329'),
    ('iyn', u'iː\u0329'),
    ('eyn', u'eɪ\u0329'),
    ('oyn', u'ɔɪ\u0329'),
    ('ehn', u'ɛ\u0329'),
    ('uhn', u'ʊ\u0329'),
    ('ayn', u'aɪ\u0329'),
    ('own', u'oʊ\u0329'),
    ('awn', u'aʊ\u0329'),
    ('aon', u'ɔː\u0329'),
    ('aan', u'ɑː\u0329'),
    ('ihn', u'ɪ\u0329'),
    ('ern', u'ɝ\u0329'),
    ('uwn', u'uː\u0329'),
    ('aen', u'æ\u0329'),
    ('aan', u'ɑː\u0329'),
    ('{B_TRANS}', u'{B_TRANS}'),
    ('{E_TRANS}', u'{E_TRANS}'),
    ('CUTOFF', u'CUTOFF'),
    ('ERROR', u'ERROR'),
    ('EXCLUDE', u'EXCLUDE'),
    ('UNKNOWN_WW', u'UNKNOWN_WW'),
    ('UNKNOWN', u'UNKNOWN'),
    ('VOCNOISE', u'VOCNOISE'),
    ('HESITATION_TAG', u'HESITATION_TAG'),
    ('LENGTH_TAG', u'LENGTH_TAG'),
    ('VOCNOISE_WW', u'VOCNOISE_WW'),
    ('NOISE', u'NOISE'),
    ('NOISE_WW', u'NOISE_WW'),
    ('IVER', u'IVER'),
    ('LAUGH', u'LAUGH'),
    ('HESITATION_TAG', u'HESITATION_TAG'),
]


class BuckeyePreparator(AbstractPreparator):
    """Convert the Buckeye corpus to the abkhazia format

    This class specializes the AbstractPreparator for the Buckeye
    corpus and implements the steps 2 to 7.

    """
    # TODO Is it a bug or needed feature ?
    # If generating the data for the first time, run all
    # steps. Otherwise, start from step 6 to just link the wavs rep.

    def _2_link_wavs(self):
        wav_src = os.path.join(self.input_dir, 'wav')

        # if folder already exists and has link, unlink and recreate link
        if os.path.isdir(self.wavs_dir):
            if os.path.islink(self.wavs_dir):
                os.unlink(self.wavs_dir)
                os.symlink(wav_src, self.wavs_dir)
            # if folder already exists and is unlinked, remove folder and
            # re-create symbolic link
            else:
                shutil.rmtree(self.wavs_dir)
                os.symlink(wav_src, self.wavs_dir)
        # if wavs folder doesn't exist, create symbolic link to speech data
        else:
            os.symlink(wav_src, self.wavs_dir)
        print('finished linking wav files')

    def _3_make_segment(self):
        output_file = os.path.join(self.data_dir, 'segments.txt')
        utt_dir = os.path.join(self.input_dir, 'txt')
        wrd_dir = os.path.join(self.input_dir, 'words_foldings')

        outfile = open (output_file, "w")
        input_txt = list_txt_files(utt_dir)
        for utts in input_txt:
            length_utt = []
            with open (utts) as infile_txt:
                current_index = 0
                last_offset = 0
                lines = infile_txt.readlines()
                bname = os.path.basename(utts)
                bname_word = bname.replace('txt', 'words_new')
                bname_wav = bname.replace('txt', 'wav')
                utt = bname.replace('.txt', '')
                length_utt = [len(line.strip().split()) for line in lines]
                wrd = os.path.join(wrd_dir, bname_word)
                with open (wrd) as infile_wrd:
                    lines_2 = infile_wrd.readlines()
                    #print (wrd)
                    del lines_2[:9]
                    assert len(lines_2) == sum(length_utt), '{} {}'.format(len(lines_2), sum(length_utt))
                    for n in range(len(length_utt)):
                        if (n == 0):
                            onset = '0.000'
                            outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + onset + ' ')
                            index_offset = length_utt[n]
                            offset_line = lines_2[index_offset-1]
                            match_offset = re.match('\s\s+(.*)\s+(121|122)\s(.*)', offset_line)
                            if not match_offset:
                                print(offset_line)
                                raise IOError
                            offset = match_offset.group(1)
                            outfile.write(str(offset))
                            current_index = index_offset
                            last_offset = offset
                            outfile.write('\n')
                        else:
                            onset = last_offset
                            outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + str(onset) + ' ')
                            index_offset = length_utt[n]+current_index
                            offset_line = lines_2[index_offset-1]
                            match_offset = re.match('\s\s+(.*)\s+(121|122)\s(.*)', offset_line)
                            if not match_offset:
                                print(offset_line)
                                raise IOError
                            offset = match_offset.group(1)
                            outfile.write(str(offset))
                            current_index = index_offset
                            last_offset = offset
                            outfile.write('\n')
        print ('finished creating segments file')

    def _4_make_speaker(self):
        output_file = os.path.join(self.data_dir, 'utt2spk.txt')
        utt_dir = os.path.join(self.input_dir, 'txt')

        outfile = open (output_file, "w")
        input_txt = list_txt_files(utt_dir)
        for utts in input_txt:
            with open (utts) as infile_txt:
                lines = infile_txt.readlines()
                bname = os.path.basename(utts)
                utt = bname.replace('.txt', '')
                speaker_id = re.sub(r"[0-9][0-9](a|b)\.txt", "", bname)
                for idx, val in enumerate(lines, start=1):
                    outfile.write(utt + '-sent' + str(idx) + ' ' + speaker_id + '\n')
        print ('finished creating utt2spk file')


    def _5_make_transcription(self):
        output_file = os.path.join(data_dir, 'text.txt')
        utt_dir = os.path.join(raw_buckeye_path, 'txt')

        outfile = open (output_file, "w")
        input_txt = list_txt_files(utt_dir)
        for utts in input_txt:
            with open (utts) as infile_txt:
                lines = infile_txt.readlines()
                bname = os.path.basename(utts)
                utt = bname.replace('.txt', '')
                for idx, val in enumerate(lines, start=1):
                    outfile.write(utt + '-sent' + str(idx) + ' ')
                    words = val.split()
                    if len(words) > 1:
                        for w in words[:-1]:
                            outfile.write(w + ' ')
                        outfile.write(str(words[-1]) + '\n')
                    else:
                        for w in words:
                            outfile.write(w)
                        outfile.write('\n')
            print ('finished creating text file')


    def _6_make_lexicon(self):
        output_file = os.path.join(data_dir, 'lexicon.txt')
        wrd_dir = os.path.join(raw_buckeye_path, 'words_foldings')

        dict_word = {}
        outfile = open (output_file, "w")
        input_txt = list_word_files(wrd_dir)
        for utts in input_txt:
            with open (utts) as infile_txt:
                #for each line of transcription, store the words in a dictionary and increase frequency
                lines = infile_txt.readlines()
                for line in lines:
                    line.strip()
                    format_match = re.match('\s\s+(.*)\s+(121|122)\s(.*)', line)
                    if format_match:
                        word_trs = format_match.group(3)
                        word_format_match = re.match("(.*); (.*); (.*); (.*)", word_trs)
                        if word_format_match:
                            word = word_format_match.group(1)
                            phn_trs = word_format_match.group(3)
                            """
                            Doing some foldings for spoken noise"
                            pattern1 = re.compile("<UNK(.*)")
                            if pattern1.match(word):
                                phn_trs = phn_trs.replace('UNKNOWN', 'SPN')
                            pattern2 = re.compile("<(CUT|cut)(.*)")
                            if pattern2.match(word):
                                phn_trs = phn_trs.replace('CUTOFF', 'SPN')
                            pattern3 = re.compile("<LAU(.*)")
                            if pattern3.match(word):
                                phn_trs = phn_trs.replace('LAUGH', 'SPN')
                            pattern4 = re.compile("<(EXT|EXt)(.*)")
                            if pattern4.match(word):
                                phn_trs = phn_trs.replace('LENGTH_TAG', 'SPN')
                            pattern5 = re.compile("<ERR(.*)")
                            if pattern5.match(word):
                                phn_trs = phn_trs.replace('ERROR', 'SPN')
                            pattern6 = re.compile("<HES(.*)")
                            if pattern6.match(word):
                                phn_trs = phn_trs.replace('HESITATION_TAG', 'SPN')
                            pattern7 = re.compile("<EXCL(.*)")
                            if pattern7.match(word):
                                phn_trs = phn_trs.replace('EXCLUDE', 'SPN')
                            """
                            if word not in dict_word:
                                dict_word[word] = phn_trs

        for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
            outfile.write (w + ' ' + f + '\n')
        print ('finished creating lexicon file')


    def _7_make_phones(self, silences=None, variants=None):
        phones = {}
        for phone, ipa in BUCKEYE_PHONES:
            phones[phone] = ipa
        silences = [u"SIL_WW", u"NSN"]  # SPN and SIL will be added automatically
        variants = []  # could use lexical stress variants...

        # TODO code taken from GP_Mandarin... share it !
        output_file = os.path.join(self.data_dir, 'phones.txt')
        with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
            for phone in phones:
                out.write(u"{0} {1}\n".format(phone, phones[phone]))

        if not(silences is None):
            output_file = os.path.join(self.data_dir, 'silences.txt')
            with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
                for sil in silences:
                    out.write(sil + u"\n")

        if not(variants is None):
            output_file = os.path.join(self.data_dir, 'variants.txt')
            with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
                for l in variants:
                    out.write(u" ".join(l) + u"\n")
        print("finished creating phones.txt, silences.txt, variants.txt")
