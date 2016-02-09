# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""Setup script for the abkhazia package"""

import os
from setuptools import setup, find_packages

VERSION = '0.2'

# On Reads The Docs we don't install any package
ON_RTD = os.environ.get('READTHEDOCS', None) == 'True'
REQUIREMENTS = [] if ON_RTD else [
    #'abnet',
    #'ABXpy',
    #'cpickle',
    #'h5features',
    #'matplotlib',
    #'numpy >= 1.8.0',
    #'pandas',
    #'yaafelib',
    #'progressbar'
]

setup(
    name='abkhazia',
    version=VERSION,
    description='ABX and kaldi experiments on speech corpora made easy',
    long_description=open('README.md').read(),
    author='Thomas Schatz, Mathieu Bernard, Roland Thiolliere, Xuan Nga Cao',
    author_email='mmathieubernardd@gmail.com',
    url='https://github.com/bootphon/abkhazia',
    license='Apache-2.0',
    packages=find_packages(exclude=['test']),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
)
