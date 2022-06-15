# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os, typing, datetime, glob, warnings, pathlib, pkg_resources
from setuptools import setup as setuptools_setup
from .cmd import bdist_app,cleanup
from ..utility.os import walk_relative_file
from ..utility.pkg import cov_to_program_name, cov_program_name_to_module_name, walk_requirements

def on_version(v:str, p:str = None, b:str = None) -> typing.Iterable[typing.Dict[str,str]]:
    '''setuptools版本生成器
    '''
    v = v if v else '0.0.1'

    if p is None:
        pass
    elif p in ['a', 'alpha']:
        v = v + 'a'
    elif p in ['b', 'beta']:
        v = v + 'b'
    elif p in ['c', 'rc']:
        v = v + 'c'

    if p is None or b is None:
        pass
    elif b in ['', '_', '-']:
        v = v + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    else:
        v = v + b

    yield dict(version = v)

def on_description(description:str = None) -> typing.Iterable[typing.Dict[str,str]]:
    '''setuptools描述生成器
    '''
    if description:
        yield dict(description = description)

    if os.path.exists("README.md"):
        with open("README.md", "r", encoding = 'utf-8') as f:
            yield dict(
                long_description_content_type = "text/markdown",
                long_description = f.read()
            )

def on_requirement(*req_dirs: os.PathLike) -> typing.Iterable[typing.Dict[str,str]]:
    '''setuptools依赖生成器
    '''
    setup_option = {}

    all_req_dir = *req_dirs, os.path.join(os.getcwd(), 'req')
    for req_dir in all_req_dir:
        for name in os.listdir(req_dir):
            pkgs = list(walk_requirements(os.path.join(req_dir, name)))
            if 'requirements.txt' == name:
                # Windows 自动添加pywin32的依赖，用于生成windows服务。
                if 'nt' == os.name and not any([ pkg.startswith('pywin32') for pkg in pkgs ]):
                    try:
                        dist = pkg_resources.get_distribution('pywin32')
                        pkgs.append(f'{dist.key} == {dist.version}')
                    except:
                        pkgs.append('pywin32')
                setup_option.update(install_requires = pkgs)
            else:
                basename, _ =  name.split('-')
                setup_option.setdefault("extras_require", {})
                setup_option["extras_require"].update({ basename : pkgs })

    yield setup_option

def on_data_dirs(**data_dir_info:typing.Tuple) -> typing.Iterable[typing.Dict[str,str]]:
    '''setuptools数据文件生成器
    '''
    data_dir_info.setdefault('bin', ('bin', '*'))

    data_file_info = {}
    for data_dir_name, (data_dir_root, *data_file_expressions) in data_dir_info.items():
        if not data_file_expressions:
            warnings.warn(f"Invalid '{data_dir_name}' data directory parameter - Skip it")
            continue

        for data_relative_file in walk_relative_file(data_dir_root, *data_file_expressions):
            data_file_dir_name = os.path.join(data_dir_name, os.path.dirname(data_relative_file)).strip('/')
            if data_file_dir_name not in data_file_info: data_file_info.update({ data_file_dir_name : set() })
            data_file_info[data_file_dir_name].add(os.path.join(data_dir_root, data_relative_file))

    yield dict(data_files = [ (n, list(s)) for n, s in data_file_info.items() ])

def setup(*on_option_generators:typing.Iterable[typing.Dict[str,str]], **setup_option:typing.Any):
    '''执行setup设置方法
    '''
    name = setup_option.get("name")
    if not name:
        # warnings.warn("Miss 'name' - Abort")
        raise Exception("Miss 'name' - Abort")

    # Merge option
    for on_option_generator in on_option_generators:
        for on_option in on_option_generator:
            setup_option.update(on_option)

    # Update cmdclass
    setup_option.setdefault("cmdclass", {})
    setup_option['cmdclass'].update(
        bdist_app = bdist_app,
        cleanup = cleanup
    )

    # Autogenerate entry_points
    if os.path.exists(name):
        setup_option.setdefault('entry_points', {})
        setup_option['entry_points'].setdefault('console_scripts', [])
        for file_path in glob.glob(f'{name}/*/__main__.py'):
            name, *module_names, _, = file_path.split(os.sep)
            program_name = cov_to_program_name(name, *module_names)
            module_name = cov_program_name_to_module_name(program_name)
            setup_option['entry_points']['console_scripts'].append(f"{program_name} = {module_name}.__main__:main")

    # Autogenerate scripts
    # p = pathlib.Path("binexe")
    # if p.exists():
    #     setup_option.setdefault('scripts', [])
    #     for file_path in p.glob('*'):
    #         setup_option['scripts'].append(file_path.as_posix())

    # Run setup
    setuptools_setup(**setup_option)