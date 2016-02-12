<!-- -*-org-*- this comment force org-mode in emacs -->

* Corpora preparation *

- WSJ (entire corpus) fatal error:

  There is several utterance-ids used several times in 'text.txt' 5608
  - [X] no duplicates in trs input files (all have different abspath)
  - [ ] check for duplicates in different subfolders

- LibriSpeech train-clean-100
  - [ ] have a --type option to select subpart of the corpus
  (test-clean, train-clean-100, etc)

- GlobalPhone
  - [ ] debug Mandarin
  - [ ] debug Vietnamese

- Buckeyepreparator
    Some utterances are overlapping in time, see details in log file
    /home/mbernard/data/abkhazia/corpora/Buckeye/logs/data_validation.log
    s0902a-sent19 s0902a-sent20

- test CSJ preparation !

* Corpora validation *

- [ ] fix this bug of overlapping utterances (at least in
  Buckeye, see for other corpora)

* Documentation *

Import wiki in docs/ and update it!

* Have a single abkhazia executable *
- Have a unique abkhazia command, with subcommands (git like)
- Load config, init log and load share only once, at top level.
- install it with setuptools
- on KeyboardInterrupt, delete any non terminated data/directory
