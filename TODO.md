# TODO

## Corpora preparation

- Smart overwrite of exitisting wavs

    Consume a lot of time, really annoying when debugging preparators
    - [X] remove the --overwrite parameter and do it by default
    - [ ] change the preparator interface to have list_audio_files()
      abstract. Implement make_wavs in AbstractPreparator.

- debug WSJ (entire corpus)

- LibriSpeech train-clean-100

    fatal error: Utterance-ids in 'segments.txt' and 'text.txt' are
    not consistent, see details in log
    /home/mbernard/data/abkhazia/corpora/LibriSpeech/logs/data_validation.log

- GlobalPhone
  - [ ] debug Mandarin
  - [ ] debug Vietnamese

- test CSJ preparation !

## Corpora validation

- [X] add a progress bar while scanning wavs
- [ ] fix this bug of overlapping utterances (at least in
  Buckeye, see for other corpora)
