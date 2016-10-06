# Abkhazia

**Online documentation can be found [here](https://abkhazia.readthedocs.io/en/latest/)**

The Abkhazia project makes it easy to obtain simple baselines for
supervised ASR (using [kaldi](http://kaldi-asr.org)) and ABX tasks
(using [ABXpy](https://github.com/bootphon/ABXpy)) on the large corpora
of speech recordings typically used in speech engineering, linguistics
or cognitive science research. To this end, Abkhazia provides the
following:

* the definition of a standard format for speech corpora, largely
  inspired from the typical format used for Kaldi recipes
* a ``abkhazia`` command-line tool for importing speech corpora to that
  standard format and performing various tasks on it,
* a Python library that can be extended to new corpora and new ASR
  models

  * verifying the internal consistency of the data
  * extracting some standard statistics about the composition of the
    corpus
  * training supervised ASR models on the corpus with Kaldi
  * computing ABX discriminability scores in various ABX tasks defined
    on the corpus

## Licence

**Copyright 2015, 2016 by Mathieu Bernard, Thomas Schatz, Xuan-Nga Cao, Roland Thiollière, Emmanuel Dupoux**

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
