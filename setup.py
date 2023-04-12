# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os, datetime
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

def gen_version(semver, pre_release_or_none = None, pre_number_or_none = None):
    final_version_string = semver
    
    if pre_release_or_none:
        final_pre_number = pre_number_or_none or 0
        final_timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        pre_releases = pre_release_or_none.split("+")

        if ('rc' in pre_releases) or ('c' in pre_releases):
            final_version_string = "%src%d.post%s" % (final_version_string, final_pre_number, final_timestamp_str)
        else:
            if 'a' in pre_releases:
                final_version_string = "%sa%d" % (final_version_string, final_pre_number)
            elif 'b' in pre_releases:
                final_version_string = "%sb%d" % (final_version_string, final_pre_number)
                
            if 'dev' in pre_releases:
                final_version_string = "%s.dev%d" % (final_version_string, final_timestamp_str)

    return final_version_string

setup(
    name="assemtools",
    version=gen_version("0.0.2", "a+dev"),
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
