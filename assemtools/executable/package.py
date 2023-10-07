#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys, getopt, subprocess
from ..constant.artifact_defs import CONFIG_FILE_DEFAULT_DEF, ArtifactTypeDefs

USAGE = f'''
命令: python -m assemtools.executable.package [OPTION]...

选项:
-h,--help
    命令使用说明

-d,--dist-dir=<path>
    成果物文件输出目录

-r,--requirements
    打包前需要安装时的依赖

-i,--index-url
    修改默认pypi仓库的地址，传递给pip命令。

--trusted-host
    增加默认信任的域名，传递给pip命令

--pre
    使用“pre-release”命令

--pypi-upload=<仓库名字>
    上传pypi仓库

--artifact-type=<app/rpm/deb>
    制品类型。app时，视情况生成tar/zip格式，其他请根据操作系统的情况进行正确设置。

--artifact-plugin=<module>
    处理制品的插件模块路径，工具会以“python -m <插件路径> <成果物路径>”的方式调用该插件

--cleaup=<common/all>
    打包完成后，普通清理会保留编译目录等缓存目录；完全清理会删除。
'''

def parse_command_arguments(*cmd_args: str) -> tuple[dict[str, str], list[str]]:
    setting = {}
    setting.setdefault('artifact_plugins', [])

    opts, args = getopt.getopt(list(cmd_args),'hd:r:i:', ['help', 'dist-dir=', 'requirements=', 'index-url=', 'trusted-host=', 'pre', 'pypi-upload=', 'artifact-type=', 'artifact-plugin=', 'cleanup='])
    for opt,val in opts:
        if opt in ('-h','--help'):
            print(USAGE)
            sys.exit(0)
        elif opt in ('-d', '--dist-dir'):
            setting.update(dist_dir = val)
        elif opt in ('-r', '--requirements'):
            setting.update(requirement_files = val)
        elif opt in ('-i', '--index-url'):
            setting.update(index_url = val)
        elif opt in ('--trusted-host'):
            setting.update(trusted_host = val)
        elif opt in ('--pre', ):
            setting.update(pre_release = True)
        elif opt in ('--pypi-upload', ):
            setting.update(pypi_upload = val)
        elif opt in ('--artifact-type', ):
            setting.update(artifact_type = val)
        elif opt in ('--artifact-plugin', ):
            setting['artifact_plugins'].append(val)
        elif opt in ('--cleanup', ):
            setting.update(cleanup = val)

    return setting, list(args)

def main():
    setting, cmd_args = parse_command_arguments(*sys.argv[1:])

    command_lines = [ sys.executable, "setup.py" ]

    # bdist_wheel
    command_lines.append("bdist_wheel")
    if dist_dir := setting.get("dist_dir"):
        command_lines.append(f"--bdist-dir={dist_dir}")

    # bdist_artifact
    command_lines.append("bdist_artifact")
    if setting.get('pre_release'):
        command_lines.append("--pre")
    if index_url := setting.get('index_url'):
        command_lines.append(f"--index-url={index_url}")
    if trusted_host := setting.get('trusted_host'):
        command_lines.append(f"--trusted-host={trusted_host}")
    if artifact_type := setting.get('artifact_type'):
        if 'rpm' == artifact_type:
            command_lines.append("--rpm")
        elif 'deb' == artifact_type:
            command_lines.append("--deb")
    if artifact_plugins := setting.get("artifact_plugins"):
        command_lines.append("--plugin=%s" %(":".join(artifact_plugins)))

    #upload
    if pypi_upload := setting.get('pypi_upload'):
        command_lines.append("upload")
        command_lines.append("-r")
        command_lines.append(pypi_upload)

    #cleanup
    if cleanup_type := setting.get('cleanup'):
        command_lines.append("cleanup")
        if 'all' == cleanup_type:
            command_lines.append("--all")
            
    comand_line_str = ' '.join(command_lines)
    print(f'Run command: {comand_line_str}')
    subprocess.run(comand_line_str, shell = True)

    # 处理制品后续操作
    # plugin_file = []
    # for plugin in setting['artifact_plugins']:
    #     subprocess.run(f"python -m {plugin} {}") 
    
if '__main__' == __name__:
    main()
