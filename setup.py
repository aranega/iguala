#!/usr/bin/env python

import sys
from setuptools import setup


version = tuple(sys.version_info[:2])

if version < (3, 7):
    sys.exit('Sorry, Python < 3.7 is not supported')

packages = ['iguala']

setup(
    name='iguala',
    version='0.4.0',
    description=("Non-linear pattern matching for Python's objects, or rexep-like for objects"),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords='pattern matching matcher regexp graph query term rewriting',
    url='https://github.com/aranega/iguala',
    author='Vincent Aranega',
    author_email='vincent.aranega@gmail.com',

    packages=packages,
    package_data={'': ['README.md', 'LICENSE', 'CHANGELOG.md']},
    include_package_data=True,
    tests_require=['pytest'],
    license='BSD 3-Clause',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
    ]
)