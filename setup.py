# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os
from setuptools import setup, find_packages

if os.path.exists("doc/README.md"):
    with open("doc/README.md", "r") as fh:
        long_description = fh.read()
else:
    long_description = ""

def get_installing_requirements():
    requirements = []

    file_path = os.path.join(os.getcwd(), 'requirements.txt' )

    if os.path.exists(file_path):
        with open(file_path, mode='r', encoding='utf-8') as f:
            requirements.extend([ l.strip() for l in f.readlines() ])

    return requirements

setup(
    name="assemtools",
    version="0.0.2.dev1",
    author='xmyeen',
    author_email="xmyeen@126.com",
    url="https://github.com/xmyeen/assemtools",
    description='',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    platforms=["all"],
    classfiers = [
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent"
    ],
    install_requires = get_installing_requirements() + [
        "wheel"
    ],
    py_modules = ["assemtools"]
)
