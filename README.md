# Abkhazia

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

**Online documentation can be found [here](https://abkhazia.readthedocs.io/en/latest/)**


## Installation

### 1. Install dependencies

Before deploying Abkahzia on your system, you need to install the
following dependencies: Kaldi, sox, shorten and festival.

#### 1.1. Install [Kaldi](http://kaldi-asr.org).

* **In brief: install_kaldi.sh**

    The ``./install_kaldi.sh`` script will download, configure and
    compile Kaldi to ``./kaldi``. This should work on any standard
    Unix distribution and fail on the first encountered error. If so,
    install Kaldi manually as detailed in the following steps.

* **If install_kaldi.sh failed**

    If so you need to install Kaldi manually with the following steps:

    * Because Kaldi is developed under continuous integration, there
      is no published release to rely on. To ensure the abkhazia
      stability, we therefore maintain a Kaldi fork that is guaranteed
      to work. Clone it in a directory of your choice and ensure the
      active branch is *abkhazia* (this should be the default):

            git clone git@github.com:bootphon/kaldi.git

    * Once cloned, you have to install Kaldi (configuration and
      compilation). Follow the instructions from
      [here](http://kaldi-asr.org/doc/install.html). Basically, you have
      to do (from the `kaldi` directory):

            cd tools
            ./extras/check_dependancies.sh
            make -j 4  # -j N does a parallel build on N CPUs
            cd ../src
            ./configure
            make depend -j 4
            make -j 4

    * Install Kaldi extras tools (SRILM and IRSTLM librairies)
      required by abkhazia. From your local kaldi directory, type:

            cd ./tools
            ./extras/install_irstlm.sh
            ./extras/install_srilm.sh

    * You will have to provide the `kaldi` directory to abkhazia during
      configuration.


#### 1.2. Sox and shorten

Abkhazia relies on [flac](https://xiph.org/flac),
[sox](http://sox.sourceforge.net) and
[shorten](http://etree.org/shnutils/shorten) for wav conversion from
various audio formats.

* sox and flac should be in repositories of every standard Unix
  distribution, for exemple in Debian/Ubuntu:

        sudo apt-get install flac sox

* shorten must be installed manually, follow these steps to
  download, compile and install it:

        wget http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz
        tar xzf shorten-3.6.1.tar.gz
        cd shorten-3.6.1
        ./configure
        make
        [sudo] make install

#### 1.3. Festival

* You need to install
  [festival](http://www.cstr.ed.ac.uk/projects/festival) on your
  system. Visit
  [this link](http://www.festvox.org/docs/manual-2.4.0/festival_6.html#Installation)
  for installation guidelines.

* On Debian/Ubuntu simply run:

        [sudo] apt-get install festival

### 2. Install Abkhazia

* First clone the Abkhazia github repository and go to the created
  `abkhazia` directory:

        git clone git@github.com:bootphon/abkhazia.git
        cd ./abkhazia

* Run the configuration script. It will check the dependancies for
  you and will initialize a default configuration file in
  `abkahzia/abkhazia.cfg`.

        ./configure

  Rerun this script and correct the prompted configuration errors
  until it succed. At least you are asked to specify the path to kaldi
  (from step 1.1) in the configuration file.


* Then install abkhazia

        python setup.py build
        [sudo] python setup.py install

* In case you want to modify and test the code, replace the last step by
  ``python setup.py develop``.


## Test

Abkhazia comes with a test suite, from the abkhazia root directory run
it using:

    py.test ./test

The tests are actually based on the Buckeye corpus, so you must
provide the path to the raw Buckeye distribution before launching the
tests. Enter this path in the ``buckeye-directory`` entry in the
Abkhazia configuration file.

If you run the tests on a cluster and you configured Abkhazia to use
Sun GridEngine, you must specify the temp directory to be in a shared
filesystem with ``py.test ./test --basetemp=mydir``.


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
