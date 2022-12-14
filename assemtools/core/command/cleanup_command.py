# -*- coding:utf-8 -*-
#!/usr/bin/env python
# type: ignore

import os, shutil
from distutils.core import Command
from ...utility.pkg import cov_to_safer_package_name

class cleanup(Command):
    description = 'Clean files'

    user_options = [
        ('all', 'a', "remove all build output, not just temporary by-products")
    ]

    boolean_options = ['all']

    def initialize_options(self):
        self.all = None
        self.dist_dir = None

    def finalize_options(self):
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))

    def clean_egg_info(self):
        egginfo_dir = '%s.egg-info' % (cov_to_safer_package_name(self.distribution.get_name()))
        if os.path.exists(egginfo_dir):
            shutil.rmtree(egginfo_dir)

    def clean_dist_file(self):
        for bdist_type, _, file in self.distribution.dist_files:
            print(f'Remove {bdist_type}: {file}')
            if os.path.exists(file):
                os.remove(file)

        if not os.listdir(self.dist_dir):
            os.removedirs(self.dist_dir)

    def run(self):
        clean_scripts = self.reinitialize_command('clean')
        clean_scripts.all = True

        self.run_command('clean')

        self.clean_egg_info()

        if self.all: self.clean_dist_file()