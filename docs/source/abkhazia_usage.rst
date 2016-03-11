=================
Command-line tool
=================

Once abkhazia is installed on your system, use it from a terminal with
the ``abkhazia`` command. For now, type::

  abkhazia --help

As you see, the program is made of several subcommands which are
detailed below. It also read a configuration file (the default one is
installed with abkhazia and you can overload it by specifying the
``--config <config-file>`` option.


Configuration file
==================

The ``abkhazia.cfg`` configuration file defines a set of default
parameters that are used by the abkhazia commands. The path to this
file depends on your installation and is given by the ``abkhazia
--help`` message. Most notable parameters are:

* **data-directory** is the directory where abkhazia write its data
  (corpora, recipes and results are stored here).  During
  installation, the data directory is configured to point in a
  ``data`` folder of the abkhazia source tree. You can specify a path
  to another dircetory, maybe on another partition.

* **kaldi-directory** is the path to an installed kaldi
  distribution. This path is configured during abkhazia installation.

The other parameters are command-specifics.


Commands
========

For more details on a specific command, type ``abkhazia <command>
--help``.

prepare: [raw] -> [corpus]
--------------------------

Prepare a speech corpus from its raw distribution format to the
abkhazia format. Write the directory ``<corpus>/data``.

split: [corpus] -> [corpus], [corpus]
-------------------------------------

Split a speech corpus in train and test sets. Write the directories
``<corpus>/train`` and ``<corpus>/test``.

language: [corpus] -> [lm]
--------------------------

Generate a language model from a prepared corpus. Write the directory
``<corpus>/language``.

train: [corpus], [lm] -> [model]
--------------------------------

Train a standard speaker-adapted triphone HMM-GMM model from a
prepared corpus. Write the directory ``<corpus>/model``.

align: [model], [lm] -> [result]
--------------------------------

Generate a forced-alignment from acoustic and language models. Write
the directory ``<corpus>/align``.

decode: [corpus], [model], [lm] -> [result]
-------------------------------------------

Decode a prepared corpus from a HMM-GMM model and a language
model. Write the directory ``<corpus>/decode``.
