#!/usr/bin/env python3

"""
Upload music on a gazelle based tracker
"""

from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

setup(
    name="gazelle-uploader",
    version="0.0.1",

    description="Upload music on a gazelle based tracker",

    author="Anthony25 <Anthony Ruhier>",
    author_email="anthony.ruhier@gmail.com",

    license="Simplified BSD",

    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: BSD License",
    ],

    keywords="torrent",
    packages=["gazelle-uploader", ],
    install_requires=["argparse", "bencodepy"],
    setup_requires=['pytest-runner', ],
    tests_require=['pytest', 'pytest-cov', "pytest-mock", "pytest-xdist"],
)
