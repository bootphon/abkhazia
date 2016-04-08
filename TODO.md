<!-- -*-org-*- this comment force org-mode in emacs -->

* Functions

 - language

   - [ ] test the --optional-silences option

 - prepare

   - [ ] --keep-short-utts option
     remove short utterances here instead of during lm/am
   - [ ] word dependent position issue
     Check in validate_corpus that adding _I, _B, _E or _S suffixes to
     phones does not create conflicts, otherwise issue a warning to say
     that word_position_dependent models won't be usable.

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

 - align

   - [X] have a --njobs option
   - [X] replace force_align.sh.in by pure python
   - [ ] make sure the lm is at word level
   - [ ] extensive test on several lm/am

 - decode

   (test_set, acoustic_model, (language_model))
   Compute phone posteriograms or transcription. options:
   evaluate(transcription, gold) output = {posteriorgrams,
   transcription} speaker_adapt output: results (repertoire)

   - [ ] If no language model provided, build default flat unigram one

 - feature

   Maybe we could have a separate feature command ?

 - list

   As an alternative of the README files, display what is in
   <data-directory> For each corpus: list of present data, recipes and
   results, with the parameters/path they ran from.

* Documentation

  - [ ] have more detailed command description on 'abkhazia <command>
    --help'. Assume the user doesn't know abkhazia or kaldi.
  - [ ] have a friendly error message when running a command with
    unstasfied dependancies. For exemple, trying to train a corpus
    which have not been prepared outputs 'please prepare the corpus'
  - [ ] make a install page, deeper than in readme
  - [ ] improve the 'command line' page
  - [ ] improve the 'corpus format' page

* Bugs [1/1]

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
