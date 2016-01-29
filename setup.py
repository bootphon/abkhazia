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
    'h5features',
    'matplotlib',
    'numpy >= 1.8.0',
    'pandas',
    #'yaafelib'
]

setup(
    name='abkhazia',
    version=VERSION,
    description='Performing ABX and kaldi experiments on speech corpora in a unified way',
    long_description=open('README.md').read(),
    #keywords='HDF5 h5py features read write',
    author='Thomas Schatz, Mathieu Bernard, Roland Thiolliere, Xuan Nga Cao',
    url='https://github.com/bootphon/abkhazia',
    license='Apache-2.0',
    packages=find_packages(exclude=['test']),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
)
