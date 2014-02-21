import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup_requires = [
    'nose==1.3.0',
    'coverage==3.7.1',
    'mock==1.0.1',
]
install_requires = [
    'straight.plugin==1.4.0',
    'Twisted==13.2.0',
]

if sys.version_info[0:2] == (2, 6):
    #install_requires.append('argparse==1.1')
    setup_requires.append('unittest2==0.5.1')

setup(
    name="nirc",
    version="0.0",
    author="Alexis Sasha Acker",
    author_email="asackerwalters@gmail.com",
    description="An IRC Bot",
    license="MIT",
    packages=find_packages(),
    long_description=read('README.rst'),
    install_requires=install_requires,
    setup_requires=setup_requires,
    test_suite='nose.collector',
)
