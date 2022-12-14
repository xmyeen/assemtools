# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os, typing, warnings, glob, re

def walk_relative_file(file_root:str, *file_expressions:str) -> typing.Iterable[str]:
    if not os.path.exists(file_root):
        return

    for file_expression in file_expressions:
        if not file_expression: continue
        if file_expression.startswith('/') or ( "win32" == os.name and re.match('^[a-zA-Z]+\://', file_expression) ):
            warnings.warn(f"Invalid '{file_expression}'. Only support realative path - Skip this")
            continue

        for p in glob.glob(f'{file_root}/{file_expression}', recursive=True):
            if not os.path.isfile(p): continue
            yield os.path.relpath(p, file_root)