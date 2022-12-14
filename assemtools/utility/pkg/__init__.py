# -*- coding:utf-8 -*-
#!/usr/bin/env python

from .package_utility import *

__all__ = [ 
    "cov_to_safer_package_name", 'cov_to_safer_package_version',
    'cov_to_app_name', 'cov_to_program_name', 'cov_program_name_to_module_name',
    'write_installer',
    'walk_requirements'
]