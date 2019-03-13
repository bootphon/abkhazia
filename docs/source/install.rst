==============================
Installation and configuration
==============================

.. note::

   First of all, clone the Abkhazia github repository and go to the
   created ``abkhazia`` directory::

     git clone git@github.com:bootphon/abkhazia.git
     cd ./abkhazia

.. note::

   Abkhazia have been succesfully installed on various Unix flavours
   (Debian, Ubuntu, CentOS) and on Mac OS. It should be possible to
   install it on a Windows system as well (through CygWin), but this
   has not been tested.


Install dependencies
====================

Before deploying Abkahzia on your system, you need to install the
following dependencies: Kaldi, sox, shorten and festival.

C++ compilers
-------------

You need to have both ``gcc`` and ``clang`` installed. On
Debian/Ubuntu just have a::

  sudo apt-get install gcc clang


Flac, sox and festival
----------------------

* Abkhazia relies on `flac <https://xiph.org/flac>`_ and `sox
  <http://sox.sourceforge.net>`_ for audio conversion from various file
  formats to wav.

  They should be in repositories of every standard Unix distribution,
  for exemple in Debian/Ubuntu::

    sudo apt-get install flac sox

* Abkhazia also needs `festival
  <http://www.cstr.ed.ac.uk/projects/festival>`_ to phonemize the
  transcriptions of the Childes Brent corpus. Visit `this link
  <http://www.festvox.org/docs/manual-2.4.0/festival_6.html#Installation>`_
  for installation guidelines, or on Ubuntu/Debian use::

    sudo apt-get install festival


Shorten
-------

`shorten <http://etree.org/shnutils/shorten>`_ is used for wav
conversion from the original *shn* audio files, it must be installed
manually. Follow these steps to download, compile and install it::

    wget http://shnutils.freeshell.org/shorten/dist/src/shorten-3.6.1.tar.gz
    tar xzf shorten-3.6.1.tar.gz
    cd shorten-3.6.1
    ./configure
    make
    sudo make install


Kaldi
-----

* Kaldi is an open-source toolkit for HMM based ASR. It is a
  collection of low-level C++ programs and high-level bash
  scripts. See `here <http://kaldi-asr.org>`_.

* **In brief: use install_kaldi.sh**

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
      active branch is *abkhazia* (this should be the default)::

            git clone git@github.com:bootphon/kaldi.git

    * Once cloned, you have to install Kaldi (configuration and
      compilation). Follow `those instructions
      <http://kaldi-asr.org/doc/install.html>`_. Basically, you have
      to do (from the ``kaldi`` directory)::

            cd tools
            ./extras/check_dependancies.sh
            make -j  # -j does a parallel build on multiple cores
            cd ../src
            ./configure
            make depend -j
            make -j

    * Install Kaldi extras tools (SRILM and IRSTLM librairies)
      required by abkhazia. From your local kaldi directory, type::

            cd ./tools
            ./extras/install_irstlm.sh
            ./extras/install_srilm.sh


Install Abkhazia
================


* It will check the dependancies for you and will initialize a default
  configuration file in ``share/abkhazia.conf``::

    ./configure

  The ``install_kaldi.sh`` setup the ``KALDI_PATH`` environment
  variable to point to the installed Kaldi root directory. If you have
  installed Kaldi manually, or if the ``configure`` script complains
  for a missing ``KALDI_PATH``, you need to specify it with for exemple::

    KALDI_PATH=./kaldi ./configure

  Rerun this script and correct the prompted configuration errors
  until it succed. At least you are asked to specify the path to Kaldi
  (as installed in previous step) in the configuration file.

* Finally install abkhazia::

    python setup.py build
    [sudo] python setup.py install

  In case you want to modify and test the code inplace, replace the
  last step by ``python setup.py develop``.

* To build the documentation (the one you are actually reading),
  install sphinx (with ``pip install Sphinx``) and, from the
  Abkhazia root directory, have a::

    sphinx-build -b html ./docs/source ./docs/html

  Then open the file ``./docs/html/index.html`` with your favorite browser.


Configuration files
===================

Abkhazia relies on two configuration files, ``abkhazia.conf`` and
``queue.conf``. Those files are generated at install time (during the
configuration step) and wrote in the ``share`` directory. But those files
are usually copied in the installation directory (e.g. in ``/usr/bin``)

.. note::

   To know where are located the configuration files on your setup,
   have a::

     abkhazia --help


``abkhazia.conf``
-----------------

The ``abkhazia.conf`` configuration file defines a set of general
parameters that are used by Abkhazia.

* **abkhazia.data-directory** is the directory where abkhazia write
  its data (corpora, recipes and results are stored here).  During
  installation, the data directory is configured to point in a
  ``data`` folder of the abkhazia source tree. You can specify a path
  to another dircetory, maybe on another partition.

* **kaldi.kaldi-directory** is the path to an installed kaldi
  distribution. This path is configured during abkhazia installation.

* **kaldi.{train, decode, highmem}-cmd** setup the parallelization to
  run the Kaldi recipes. Choose either
  ``run.pl`` to run locally or ``queue.pl`` to use a cluster managed
  with the Sun GridEngine.

* **raw corpora directories** can be specified in the ``corpus``
  section of the configuration file.

``queue.conf``
--------------

**You should adapt this file to your cluster configuration**

The ``queue.conf`` configuration file is related to parallel
processing in Kaldi when ``queue.pl`` is used. It allows to forward
options to the Sun GridEngine when submitting jobs. See `this page
<http://kaldi-asr.org/doc/queue.html>`_ for details.


Run the tests
=============

.. note::

   The tests are actually based on the Buckeye corpus, so you must
   provide the path to the raw Buckeye distribution before launching the
   tests. Enter this path in the ``buckeye-directory`` entry in the
   Abkhazia configuration file.

* Abkhazia comes with a test suite, from the abkhazia root directory run
  it using::

    pytest ./test

* To install the ``pytest`` package, simply have a::

    [sudo] pip install pytest

* If you run the tests on a cluster and you configured Abkhazia to use
  Sun GridEngine, you must specify the temp directory to be in a shared
  filesystem with ``pytest ./test --basetemp=mydir/tmp``.
