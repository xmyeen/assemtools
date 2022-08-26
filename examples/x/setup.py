# -*- coding:utf-8 -*-
#!/usr/bin/env python

from assemtools import setup, find_packages, on_version, on_description, on_requirement, on_data_dirs

setup(
    on_version('1.0.0'),
    on_description("示例样例"),
    on_requirement(),
    on_data_dirs(
        config = ('config', 'app.ini'),
        data = ('var', '**/**.csv')
    ),

    name = "x",
    author = 'xmyeen@163.com',
    author_email = "xmyeen@163.com",
    packages = find_packages(exclude = ["*.tests", "*.tests.*", "tests.*", "tests"]),
    platforms = ["all"],
    url = "https://github.com/xmyeen/assemtools",
    license = "MIT",
    classifiers = [
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X"
    ],
    python_requires='>=3.8'
)