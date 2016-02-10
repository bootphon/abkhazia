# Abkhazia

Tools for performing standard ABX and kaldi experiments on speech
corpora in a unified way

Documentation **actually not up to date** can be found
[here](https://github.com/bootphon/abkhazia/wiki)


## Installation

### Install dependencies

Before deploying abkahzia on your system, you need to install the
following dependencies. If they are not available on your system, the
abkhazia configuration script will fail.

* [Kaldi Speech Recognition Toolkit](http://kaldi-asr.org).

	Follow installation guidelines
    [here](http://kaldi-asr.org/doc/install.html). You will have to
    provide the Kaldi directory to abkhazia during configuration.

* [sox](http://sox.sourceforge.net), [flac](http://xiph.org/flac) and
  [shorten](http://etree.org/shnutils/shorten) for wav conversion from
  various audio formats.

	sox and flac should be in repositories of every standard Unix
    distribution, for exemple in Debian/Ubuntu:

    	sudo apt-get install flac sox

   	shorten must be installed manually, follow these steps to
       download, compile and install it:

    	wget http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz
   		tar xzf shorten-3.6.1.tar.gz
   		cd shorten-3.6.1
   		./configure
   		make
   		sudo make install


### Install Abkahzia

First run the configuration script. It will check the dependancies for
you and will initialize a default configuration file in
`abkahzia/share/abkahzia.cfg`.

    ./configure.sh

 Rerun this script and correct the prompted configuration errors until
 it succed. Then move to next step:

    python setup.py install
    python setup.py build


## Licence

**Copyright 2015, 2016 by Thomas Schatz, Xuan Nga Cao, Roland Thiollière, Mathieu Bernard**

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
