# -*- coding:utf-8 -*-
#!/usr/bin/env python

from setuptools import find_packages, find_namespace_packages
from .setup import setup, on_version, on_description, on_requirement, on_data_dirs, on_entry_points

__all__ = [ 
    "find_packages", "find_namespace_packages",
    "setup",
    "on_version", "on_description", "on_requirement", "on_data_dirs", "on_entry_points"
]