<!-- -*-org-*- this comment force org-mode in emacs -->

* Open bugs [0/3]
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
* Feature requests
** TODO for a next release
 - features
   - centralize/refactor the legacy code related to features
   - option to export features from ark to h5f, see
     [[https://github.com/bootphon/features_extraction/blob/master/kaldi_features.py][kaldi_features.py]] from feature_extraction package
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
 - abkhazia align --post --with-words
   Update the probabilities estimation to be on words, not on phones
 - decode
   options:
      evaluate(transcription, gold)
      output = {posteriorgrams, transcription}
      speaker_adapt
      output: results (repertoire)
 - documentation
  - [ ] have more detailed command description on 'abkhazia <command>
    --help'. Assume the user doesn't know abkhazia or kaldi.
  - [ ] improve the 'command line' page
  - [ ] improve the 'corpus format' page
** TODO updating abkhazia.cfg
   - Need of an automated way to update new versions of the installed
     configuration file in the ./configure script.
   - Do that along with the next update of the config file
* Fixed bugs [3/3]
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
** DONE abkhazia language buckeye -v
   CLOSED: [2016-05-30 lun. 23:30]
*** gzip: stdout: Broken pipe
   -: line 340912: warning: 13585 1-grams read, expected 13590
   -: line 340912: warning: 98096 2-grams read, expected 98106
   -: line 340912: warning: 229218 3-grams read, expected 229232
*** broken pipe does not impact anything
*** warning on missing n-grams
    this is the effect of OOV pruning in kaldi
    tools/srilm/bin/change-lm-vocab, so not a problem nor a bug
