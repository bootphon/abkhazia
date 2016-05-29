<!-- -*-org-*- this comment force org-mode in emacs -->

* for 0.3 release (pre tutorial) [6/7]
** DONE align on words only (discard phones)
   CLOSED: [2016-05-20 ven. 17:54]
** DONE LM optional silences by default
   CLOSED: [2016-05-20 ven. 17:59]
** DONE split must write {testing/train}/data
   CLOSED: [2016-05-23 lun. 10:41]
** DONE prepare buckeye: strange lexicon issue
   CLOSED: [2016-05-23 lun. 10:54]
   following words have no transcription in lexicon: set(['and', 'a',
   'okay', "you're", 'i', 'of', 'it', 'uh', 'in', 'ohio', 'rough',
   'know'])
** DONE compute alignment posteriograms with Kaldi [3/3]
   CLOSED: [2016-05-26 jeu. 10:50]
*** DONE have a working beta version
    CLOSED: [2016-05-24 mar. 21:39]
*** DONE avoid share/align_fmllr.sh and implement it in python
    CLOSED: [2016-05-26 jeu. 10:50]
    Use steps/align_fmllr_lats.sh + posterior computation from lattice
*** DONE refactor the align recipe
    CLOSED: [2016-05-26 jeu. 10:50]
    no more separation, use lattice for no-post alignments
    more clear, with comments and explanation on tra/post files
** DONE install_kaldi unix/mac
   CLOSED: [2016-05-26 jeu. 16:42]
** TODO updating abkhazia.cfg
   Need of an automated way to update new versions of the installed
   configuration file in the ./configure script.
* Open bugs [0/5]
** festival
** TODO abkhazia language buckeye -v
   gzip: stdout: Broken pipe
   -: line 340912: warning: 13585 1-grams read, expected 13590
   -: line 340912: warning: 98096 2-grams read, expected 98106
   -: line 340912: warning: 229218 3-grams read, expected 229232
** TODO abkhazia language librispeech-test-clean -n 3 -l word
Fail in word level, regardless silences. Work on phone

running utils/format_lm_sri.sh --srilm_opts "-subset -prune-lowprobs -unk" /home/mathieu/lscp/data/abkhazia/librispeech-test-clean/language /home/mathieu/lscp/data/abkhazia/librispeech-test-clean/language/recipe/data/local/language/G.arpa.gz /tmp/tmpFWGkJL
Converting '/home/mathieu/lscp/data/abkhazia/librispeech-test-clean/language/recipe/data/local/language/G.arpa.gz' to FST
gzip: stdout: Broken pipe
-: line 91932: warning: 8014 1-grams read, expected 8141
-: line 91932: warning: 35217 2-grams read, expected 35595
-: line 91932: warning: 48688 3-grams read, expected 49258
ngram: ../../include/LHash.cc:519: void LHashIter<KeyT, DataT>::sortKeys() [with KeyT = unsigned int; DataT = Trie<unsigned int, BOnode>]: Assertion `j == numEntries' failed.
/home/mathieu/lscp/dev/kaldi/tools/srilm/bin/change-lm-vocab: line 78: 12596 Done                    gzip -dcf $oldlm
12597                       | ${GAWK-gawk} '
# read the vocab file
NR == 1 && vocab {
# always include sentence begin/end
is_word["<s>"] = is_word["</s>"] = 1;
while ((getline word < vocab) > 0) {
is_word[to_lower ? tolower(word) : word] = 1;
}
close(vocab);
}
# process old lm
NF==0 {
print; next;
}
/^ngram *[0-9][0-9]*=/ {
order = substr($2,1,index($2,"=")-1);
print;
next;
}
/^\\[0-9]-grams:/ {
currorder=substr($0,2,1);
print;
next;
}
/^\\/ {
print; next;
}
currorder {
for (i = 2 ; i <= currorder + 1; i ++) {
if (!((to_lower ? tolower($i) : $i) in is_word)) next;
}
print;
next;
}
{ print }
' vocab=$vocab to_lower=$tolower
12598 Aborted                 | ngram -lm - -vocab "$ngram_vocab" -renorm -write-lm "$newlm" $options
** TODO abkhazia features/language brent
ldes_brent/language /home/mbernard/dev/abkhazia/egs/align_childes_brent/acoustic/recipe/exp/mono
steps/train_mono.sh --nj 4 --cmd run.pl data/acoustic /home/mbernard/dev/abkhazia/egs/align_childes_brent/language /home/mbernard/dev/abkhazia/egs/align_childes_brent/acoustic/recipe/exp/mono
split_data.sh: warning, #lines is (utt2spk,feats.scp) is (112865,112862); you can
use utils/fix_data_dir.sh data/acoustic to fix this.

** TODO abkhazia decode
   what is the bug??
** TODO abkhazia align --post --with-words
   Update the probabilities estimation to be on words, not on phones
* Functions
 - prepare childes
   - test with others than Brent, have a subcorpus selection option?
   - strange words in trs:
     xcuse -> excuse
     fiin / fiin o
 - features
   - centralize/refactor the legacy code related to features
   - option to export features from ark to h5f, see
     [[https://github.com/bootphon/features_extraction/blob/master/kaldi_features.py][kaldi_features.py]] from feature_extraction package
 - language
   - [X] test the --optional-silences option
   - is it an error to prune lexicon when training/testing a LM on a corpus ?
 - acoustic
   - [ ] --retrain option
     it should be possible to retrain a trained model on a new corpus
     (for instance, specifically retrain silence models, or retrain on a
     bunch of new corpus)
   - [ ] questions vs data-driven option
   - [ ] neural nets training (RT)
   - [ ] test the acoustic model
     providing WER (word error rate) for every model, eventual
     automatic parameter search ?
   - [ ] warning issues in kaldi gmm with buckeye
     WARNING (gmm-init-model:InitAmGmm():gmm-init-model.cc:55) Tree has
     pdf-id 81 with no stats; corresponding phone list: 82

     ** The warnings above about 'no stats' generally mean you have phones **
     ** (or groups of phones) in your phone set that had no corresponding data. **
     ** You should probably figure out whether something went wrong, **
     ** or whether your data just doesn't happen to have examples of those **
     ** phones. **
 - decode
   - options:
      evaluate(transcription, gold)
      output = {posteriorgrams, transcription}
      speaker_adapt
      output: results (repertoire)
* Documentation
  - [ ] have more detailed command description on 'abkhazia <command>
    --help'. Assume the user doesn't know abkhazia or kaldi.
  - [ ] improve the 'command line' page
  - [ ] improve the 'corpus format' page
* Fixed bugs [2/2]
** DONE installation on Mac
   CLOSED: [2016-05-20 ven. 13:02]
   XN -- Pour le testing sur mac, ça ne marche pas ou en tout cas, je
   n'ai pas pu avancer.  J'ai lancé install_kaldi.sh et il a fait
   pleins de choses mais il a crashé vers la fin.  J'ai aussi essayé
   de cloner la dernière version de kaldi mais ça ne semble pas
   marcher sur abkhazia car il plante sur abkhazia language.
** DONE language
   Fail on n!=3 for n-grams. Used to work with previous version of kaldi.
*** py.test -vx ./test/test_language.py | egrep "^\[.*ERROR"

    ["2016-03-30 17:51:06,422 - DEBUG - ERROR
    (arpa2fst:Read():arpa-file-parser.cc:228) in line 70: Invalid or
    unexpected directive line '\\2-grams:', expected \\end\\.\n",
    "2016-03-30 17:51:06,422 - DEBUG - ERROR
    (arpa2fst:Read():arpa-file-parser.cc:228) in line 70: Invalid or
    unexpected directive line '\\2-grams:', expected \\end\\.\n",
    '2016-03-30 17:51:06,423 - DEBUG - ERROR: FstHeader::Read: Bad FST
    header: standard input\n']

*** details

 - [X] A working kaldi commit
    a9b65137b4ab90845c1357724d5ddaa805972830 (10 Feb. 2016)
 - [X] where in abkhazia script the bug occurs?
   - in _format_lm() -> utils/format_lm_sri.sh
   - in kaldi-trunk/tools/srilm/bin/change-lm-vocab -> add an empty 3-gram
 - [X] find a kaldi commit before that bug was introduced?
   - seems to be introduced by dpovey on commit (after?)
     a9b65137b4ab90845c1357724d5ddaa805972830 (10 Feb. 2016)
 - [X] eventually write a pull request?

*** solution
 - submited https://github.com/kaldi-asr/kaldi/pull/639
 - the bug is fixed within kaldi, see https://github.com/kaldi-asr/kaldi/issues/643
