# -*- coding:utf-8 -*-
#!/usr/bin/env python

import pkg_resources, os, stat, typing
from ..string.string_utility import cov_snake_to_hump, cov_hump_to_snake
from ...constant.installer_defs import INSTALLER_CONTENT_TEMPLATE_DEF

def cov_to_safer_package_name(name:str):
    return pkg_resources.safe_name(name).replace('-', '_')

def cov_to_safer_package_version(version:str):
    return pkg_resources.safe_version(version).replace('-', '_')

def cov_to_app_name(name:str) -> str:
    return cov_snake_to_hump(cov_to_safer_package_name(name))

def cov_to_program_name(name:str, *module_names:str) -> str:
    return '-'.join(map(lambda s: cov_snake_to_hump(cov_to_safer_package_name(s)), [name, *module_names]))

def cov_program_name_to_module_name(program_name:str) -> str:
    return '.'.join(map(lambda s: cov_hump_to_snake(cov_to_safer_package_name(s)), program_name.split('-')))

def write_installer(f: typing.IO, app_name:str, app_wheel_name:str, *app_programs:str, **other_option:typing.Any):
    f.write(
        INSTALLER_CONTENT_TEMPLATE_DEF.format(
            PIP_INSTALL_OPTION_DEF = other_option.get("pip_install_option", ""),
            APP_NAME_DEF = app_name,
            APP_DESCRIPTION_DEF = "",
            APP_WHEEL_NAME = os.path.basename(app_wheel_name),
            APP_PROGRAM_NAME_DEF = " ".join(app_programs)
        )
    )
    f.flush()

    if f.name:
        os.chmod(f.name, stat.S_IRWXU  | stat.S_IRWXG | stat.S_IROTH  | stat.S_IXOTH )

def walk_requirements(req_file: os.PathLike) -> typing.Iterable[str]:
    '''递归扫描requirements.txt的包
    '''
    with open(req_file, mode='r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#'):
                continue
            elif l.startswith('-r'):
                sub_req_file = l[2:].strip()
                yield from walk_requirements(os.path.join(os.path.dirname(req_file), sub_req_file))
            else:
                yield l