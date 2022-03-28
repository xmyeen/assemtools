# -*- coding:utf-8 -*-
#!/usr/bin/env python

import re

def cov_snake_to_hump(string:str) -> str:
    return re.sub('[_][a-zA-Z]', lambda m: m.group()[1].upper(), string.strip('_'))

def cov_hump_to_snake(string:str) -> str:
    return  re.sub('[A-Z]', lambda m: '_' + m.group(0).lower(), string).strip('_')