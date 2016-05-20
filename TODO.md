<!-- -*-org-*- this comment force org-mode in emacs -->

* for 0.3 release (pre tutorial) [1/8]
** DONE align on words only (discard phones)
   CLOSED: [2016-05-20 ven. 17:54]
** TODO LM optional silences by default
** TODO prepare buckeye: strange lexicon issue
   following words have no transcription in lexicon: set(['and', 'a',
   'okay', "you're", 'i', 'of', 'it', 'uh', 'in', 'ohio', 'rough',
   'know'])
** TODO split must write {testing/train}/data
** TODO features: some files not computed, issues a warning
   issue with short utterances?
** TODO install_kaldi unix/mac
*** replace readlink/greadlink by a python oneliner
*** change path in SRILM (macosx/i686)
** TODO updating abkhazia.cfg
   Need of an automated way to update new versions of the installed
   configuration file in the ./configure script.
** TODO bug in decode
* posteriors on Childes/Brent alignement [2/3]
** DONE intégrer Childes/Brent dans abkhazia
   CLOSED: [2016-04-24 dim. 23:33]
*** corpus original (en 16 kHz)
    oberon:/fhgfs/bootphon/scratch/xcao/Brent_test_abkhazia/Brent_corpus_test_abkhazia
*** From XN
   - tous les scripts que j'ai utilisés pour générer les données
     oberon:/fhgfs/bootphon/scratch/xcao/Brent_test_abkhazia/scripts
   - les sorties si tu veux comparer quand tu auras écrit le script
     oberon:/fhgfs/bootphon/scratch/xcao/Brent_test_abkhazia/ouput_brent_abkhazia
** DONE force align HTK like
   CLOSED: [2016-04-27 mer. 00:12]
   on a une sortie alignment forcé des phones mais peut-on avoir un
   alignement des mots? Le mieux serait une sortie des 2 comme le fait
   HTK (voir pj) car je pense qu'on va en avoir besoin plus tard...

   Les sorties des alignements forcés sont dans le même répertoire que
   toutes autres données du Brent.

   Tu verras que Kaldi n'a pas pu
   aligner toutes les phrases qui sont dans text.txt mais c'est normal
   non?

   /ssh:oberon:/fhgfs/bootphon/scratch/xcao/Brent_test_abkhazia/output_brent_abkhazia/output_forced_alignment_kaldi/phone_align
   (pour les fichiers splittés) ou "forced_alignment.txt"
** TODO compute alignment posteriograms with Kaldi
** prepare childes
   - test with others than Brent, have a subcorpus selection option?
   - strange words in trs:
     xcuse -> excuse
     fiin / fiin o
* Functions
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
