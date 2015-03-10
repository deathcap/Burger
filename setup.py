#!/usr/bin/env python
# -*- coding: utf8 -*-

from distutils.core import setup

setup(
    name='Sŏlum',
    packages=['solum', 'solum/core', 'solum/util'],
    version='2.0.0',
    description='A low-level library for JVM class file maniplation.',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='http://github.com/TkTech/Solum',
    keywords=[
        'java',
        'disassembly',
        'disassembler',
        'assembler'
    ],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Disassemblers'
    ]
)
