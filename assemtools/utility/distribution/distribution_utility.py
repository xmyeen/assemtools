#!/usr/bin/env python
# -*- coding:utf-8 -*-

import typing, re
from distutils.dist import Distribution

def walk_distribution_program_name(distribution: Distribution, main_name:str) -> typing.Iterator[str]:
    if not hasattr(distribution, 'entry_points'): return

    entry_point_data = getattr(distribution, 'entry_points')
    if not entry_point_data: return 

    for script_value_strings in entry_point_data.values():
        for script_value_string in script_value_strings:
            program_name, _, program_main_name = re.split(r'\s?=\s?|\s?\:\s?', script_value_string)
            if main_name != program_main_name: continue
            yield program_name