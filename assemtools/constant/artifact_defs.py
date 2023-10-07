#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os, enum, typing

#%homedrive%%homepath%

CONFIG_FILE_NAME_DEFAULT_DEF = "assemtools.json"

CONFIG_FILE_DEFAULT_DEF = [
    f"{os.getcwd()}/{CONFIG_FILE_NAME_DEFAULT_DEF}",
    f"{os.getenv('homedrive')}{os.getenv('homepath')}\\{CONFIG_FILE_NAME_DEFAULT_DEF}" if os.name == 'nt' else f"{os.getenv('HOME')}/{CONFIG_FILE_NAME_DEFAULT_DEF}",
    f"{os.getenv('appdata')}\\assemtools\\{CONFIG_FILE_NAME_DEFAULT_DEF}" if os.name == 'nt' else f"/etc/assemtools/{CONFIG_FILE_NAME_DEFAULT_DEF}" 
]

@enum.unique
class ArtifactTypeDefs(enum.Enum):
    APP = 0
    SVC = 1

    @staticmethod
    def get_all_names() -> list[str]:
        return [ e.get_type_name() for e in ArtifactTypeDefs.__members__.values() ]

    def get_type_name(self) -> str:
        return self.name.lower()

    def is_this_type(self, val:str) -> bool:
        return self.get_type_name() == val