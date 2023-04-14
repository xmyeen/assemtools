# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os, re, typing, datetime, glob, warnings, pathlib, pkg_resources, subprocess
from setuptools import setup as setuptools_setup
from .command import bdist_artifact, cleanup
from ..utility.os import walk_relative_file
from ..utility.pkg import cov_to_program_name, cov_program_name_to_module_name, walk_requirements

def on_version(final_release:str, pre_release:str|None = None, post_release:str|int|None = None, dev_release:str|int|None = None) -> typing.Iterable[dict[str,typing.Any]]:
    '''版本生成方法

    版本格式：[N!]N(.N)*[{a|b|rc}N][.postN][.devN]
    
    标准：PEP440(https://aa-turner.github.io/peps/pep-0440/)
    
    final_release {str} SemVer2.0版本的基本字符串，如：1.0.0
    
    pre_release {str} 发布版本标识，取值：dev | a | alpha | b | beta | c | rc | release
    
    post_release {str|int} 是否附加Post-release信息。可以设置一个整数值。或者传"systime"附加系统时间。

    dev_release {str|int} 是否附加Developmental release信息。可以设置整数值，或者传“systime”附加系统时间；若存在post<systime>，则忽略。
    '''
    final_version = final_release

    if pre_release is not None:
        pre_release_match = re.match("([a-zA-Z]+)(\\d*)", pre_release)
        if pre_release_match is None: raise RuntimeError(f"Invalid Pre-release tag: {pre_release}")

        alphabetical_pre_release_value = pre_release_match and pre_release_match.group(1)
        numberal_pre_release_value = (pre_release_match and pre_release_match.group(2)) or 0

        if alphabetical_pre_release_value.lower() in ('a', 'alpha'):
            final_version += f"a{numberal_pre_release_value}"
        elif alphabetical_pre_release_value.lower() in ('b', 'beta'):
            final_version += f"b{numberal_pre_release_value}"
        elif alphabetical_pre_release_value.lower() in ('c', 'rc', 'release'):
            final_version += f"rc{numberal_pre_release_value}"
        else:
            raise RuntimeError(f"Invalid Pre-release tag: {pre_release}")
    
    if post_release is None:
        pass
    elif isinstance(post_release, int):
        final_version += f'.post{post_release}'
    elif post_release == "systime":
        final_version += f'.post{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    else:
        raise RuntimeError(f"Invalid Post-release tag: {post_release}")
        
    if dev_release is None:
        pass
    elif post_release is not None:
        pass
    elif isinstance(dev_release, int):
        final_version += f'.dev{dev_release}'
    # elif dev_release == 'git':
    #     commit_timestamp = subprocess.getoutput('git log -n 1 --pretty=format:"%cd" --date=format:"%Y%m%d%H%M%S"').strip()
    #     if not re.match("\\d+", commit_timestamp): raise RuntimeError(f"Fetch git commit log failed: {commit_timestamp}")
    #     final_version += f".dev{commit_timestamp}"
    elif dev_release == "systime":
        final_version += f'.dev{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    else:
        raise RuntimeError(f"Invalid Dev-release tag: {dev_release}")
        
    yield dict(version = final_version)

def on_description(description:str|None = None) -> typing.Iterable[dict[str,typing.Any]]:
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

def on_requirement(*req_dirs: os.PathLike) -> typing.Iterable[dict[str,typing.Any]]:
    '''setuptools依赖生成器
    '''
    setup_option = {}

    all_req_dir = *req_dirs, os.path.join(os.getcwd(), 'req')
    for req_dir in all_req_dir:
        if not os.path.exists(req_dir): continue
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

def on_data_dirs(**data_dir_info:tuple) -> typing.Iterable[dict[str,typing.Any]]:
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

def on_entry_points(*script_glob_finders: tuple[str, str, str]) -> typing.Iterable[dict[str,typing.Any]]:
    entry_point : dict[str, list[str]] = {}

    for script_name, script_glob_string, function_name in script_glob_finders:
        if script_name not in ("console_scripts", "gui_scripts"):
            warnings.warn(f"Unkown script name. Skip: {script_name}")
            continue

        if script_glob_string.startswith(("/", os.sep, ".")):
            warnings.warn(f"Path can not start with '/.': {script_glob_string}")
            continue

        if not script_glob_string.endswith("__main__.py"):
            warnings.warn(f"Path must end with '__main__.py': {script_glob_string}")
            continue
        
        glob_string = script_glob_string 
        
        if glob_string.endswith('/'):
            glob_string = glob_string[:-1]

        for file_path in glob.glob(glob_string):
            name, *module_names, _ = file_path.split(os.sep)
            
            program_name = cov_to_program_name(name, *module_names)
            module_name = cov_program_name_to_module_name(program_name)

            value = f"{program_name} = {module_name}.__main__:{function_name}"
            if script_name not in entry_point:
                entry_point.update({ script_name : [value] })
            else:
                entry_point[script_name].append(value)
    
    if entry_point:
        yield dict(entry_points = entry_point)

def setup(*on_option_generators:typing.Iterable[dict[str,str]], **setup_option:typing.Any):
    '''执行setup设置方法
    '''
    name = setup_option.get("name")
    if not name:
        raise Exception("Miss 'name' - Abort")

    # Update cmdclass
    setup_option.setdefault("cmdclass", {})
    setup_option['cmdclass'].update(
        bdist_artifact = bdist_artifact,
        cleanup = cleanup
    )

    # Merge option
    for on_option_generator in on_option_generators:
        for on_option in on_option_generator:
            setup_option.update(on_option)

    # Autogenerate scripts
    # p = pathlib.Path("binexe")
    # if p.exists():
    #     setup_option.setdefault('scripts', [])
    #     for file_path in p.glob('*'):
    #         setup_option['scripts'].append(file_path.as_posix())

    # Run setup
    setuptools_setup(**setup_option)