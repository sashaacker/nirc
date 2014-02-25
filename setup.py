import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

install_requires = [
    'straight.plugin==1.4.0',
    'irc==8.5.4',
    'six==1.5.2',
]

if sys.version_info[0:2] == (2, 6):
    #install_requires.append('argparse==1.1')
    pass

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
)
