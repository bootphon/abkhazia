====================================
abkhazia's documentation
====================================

.. note::

   The source code is available at `<www.github.com/bootphon/abkhazia>`_.


The abkhazia project makes it easy to obtain simple baselines for
supervised ASR (using `kaldi`_) and ABX tasks (using `ABXpy`_) on the
large corpora of speech recordings typically used in speech
engineering, linguistics or cognitive science research. To this end,
abkhazia provides the following:

* the definition of a standard format for speech corpora, largely
  inspired from the typical format used for kaldi recipes
* a ``abkhazia`` command-line tool for importing speech corpora to that
  standard format and performing various tasks on it,
* a Python library that can be extended to new corpora and new ASR
  models




  * verifying the internal consistency of the data

  * extracting some standard statistics about the composition of the
    corpus

  * training supervised ASR models on the corpus with kaldi

  * computing ABX discriminability scores in various ABX tasks defined
    on the corpus


Abkhazia also comes with a set of recipes for specific corpora, which
can be applied to the raw distribution of these corpora directly to
obtain a version in standard format. The only requirement is to have
access to the raw distributions. Unfortunately, unlike most other
domains, large speech corpora are most of the time not freely
available. List the list of corpora supported in abkhazia with
``abkhazia prepare --help``




.. toctree::
   :caption: Table of contents
   :maxdepth: 2

   abkhazia_format
   abkhazia
   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _kaldi: http://kaldi.sourceforge.net
.. _ABXpy: https://github.com/bootphon/ABXpy
