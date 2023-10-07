#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pkg_resources, os, stat, typing, warnings, re, sys, subprocess
from ..string.string_utility import cov_snake_to_hump, cov_hump_to_snake
from ...constant.installer_defs import INSTALLER_CONTENT_TEMPLATE_DEF

def cov_to_safer_package_name(name:str):
    return pkg_resources.safe_name(name).replace('-', '_')

def cov_to_safer_package_version(version:str):
    return pkg_resources.safe_version(version).replace('-', '_')

def cov_to_app_name(name:str) -> str:
    return cov_snake_to_hump(cov_to_safer_package_name(name))

def cov_to_program_name(name:str, *module_names:str) -> str:
    '''转换模块名字成为程序名字
    (name="my-app", module_names=["web","client"]) => myApp-web-client
    '''
    return '-'.join(map(lambda s: cov_snake_to_hump(cov_to_safer_package_name(s)), [name, *module_names]))

def cov_program_name_to_module_name(program_name:str) -> str:
    return '.'.join(map(lambda s: cov_hump_to_snake(cov_to_safer_package_name(s)), program_name.split('-')))

def write_installer(f: typing.IO, app_name:str, app_wheel_name:str, *app_programs:str, **other_option:typing.Any):
    app_hump_name = re.sub(r'[_-]([a-zA-Z])', lambda m: m.group(1).upper(), app_name)
    f.write(
        INSTALLER_CONTENT_TEMPLATE_DEF.format(
            PIP_INSTALL_OPTION_DEF = other_option.get("pip_install_option", ""),
            APP_NAME_DEF = app_name,
            APP_DESCRIPTION_DEF = "",
            APP_WHEEL_NAME = os.path.basename(app_wheel_name),
            APP_PROGRAM_NAME_DEF = " ".join(app_programs),
            APP_ADMIN_PROGRAM_NAME_DEF = f"{app_hump_name}-app-admin"
        )
    )
    f.flush()

    if f.name:
        os.chmod(f.name, stat.S_IRWXU  | stat.S_IRWXG | stat.S_IROTH  | stat.S_IXOTH )

def walk_requirements(req_file: str) -> typing.Iterable[str]:
    '''递归扫描requirements.txt的包
    '''
    with open(req_file, mode='r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#'):
                continue

            if l.startswith('-'):
                for k, v in re.findall("(\\-[\\-\\w]*)[\\s=\\s]([^$^\\s]*)", l):
                    if k in ('-r', '--requirement'):
                        yield from walk_requirements(os.path.join(os.path.dirname(req_file), v))
                    elif k in ('-e', '--editable'):
                        if extra_require_string_groups := re.findall("\\[.*\\]", v):
                            extra_require_string_group = extra_require_string_groups[0] or ""
                            editable_project_dir = v[:0 - len(extra_require_string_group)]
                        else:
                            extra_require_string_group = ""
                            editable_project_dir = v

                        if not os.path.exists(os.path.join(editable_project_dir, "setup.py")):
                            raise RuntimeError(f"Miss setup.py in '{editable_project_dir}'")

                        pkg_name = subprocess.check_output([sys.executable, 'setup.py', '--name'], cwd = editable_project_dir).decode('utf-8').strip()

                        if editable_project_dir.startswith('/'):
                            editable_project_uri = 'file://' + editable_project_dir.replace('\\', '/')
                        elif 0 > editable_project_dir.find('://'):
                            editable_project_uri = 'file://' + '/' + editable_project_dir.replace('\\', '/')
                        else:
                            editable_project_uri = editable_project_dir
                        # subprocess.run([sys.executable, '-m', 'pip', 'download', '-f', f'\'{l}\'', '--exists-action=w', '--dest=.'])
                        yield f'{pkg_name}{extra_require_string_group} @ {editable_project_uri}'
                    # elif l.startswith(('-i', '--index-url')):
                    #     continue
                    # elif l.startswith('--extra-index-url'):
                    #     continue
                    # elif l.startswith(('-f', '--find-links')):
                    #     continue
                    # elif l.startswith(('-c', '--constraint')):
                    #     continue
                    else:
                        # warnings.warn(f"Skip an unrecognizable requirement: {k} {v}")
                        continue
            # elif 0 < l.find("://"):
            #     #urllib3 @ https://github.com/urllib3/urllib3/archive/refs/tags/1.26.8.zip
            #     #pyidentify @ git+http://iris.hikvision.com.cn/chenyuzhi/pyidentify.git
            #     name, _, url_string = l.split(' ')
            #     # subprocess.run([sys.executable, '-m', 'pip', 'download', '-f', f'\'{l}\'', '--exists-action=w', '--dest=.'])
            #     yield name.strip()
            # elif os.path.isfile(l):
            #     print(l)
            else:
                yield l