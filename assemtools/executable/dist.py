# -*- coding:utf-8 -*-
#!/usr/bin/env python

from ..constant.dist_defs import CONFIG_FILE_DEFAULT_DEF, DistTypeDefs


USAGE = f'''
命令: python -m assemtools.executable.dist [OPTION]...

选项:
-h,--help
    命令使用说明

-c,--config=<path>
    工具配置文件，查找顺序依次为：{'，'.join(CONFIG_FILE_DEFAULT_DEF)}

-t,--type=<{'/'.join(DistTypeDefs.get_all_names())}>
    成果物类型。app生成tar/zip格式；svc生成systemd服务的分发格式，例如：centos系统分发格式为rpm。

-d,--dist-dir=<path>
    成果物文件输出目录

-p,--pack
    打包成果物

-u,--upload
    上传成果物，搭配“打包成果物”一起使用。若没有指定“打包成果物”命令，会自动补充该命名。

--pre
    使用“pre-release”命令

--pypi-publish=<name>
    上传PYPI成果物的仓库名字。默认值： pypi

--artifact-publish=<name>
    上传非PYPI成果物的仓库名字。需要搭配仓库插件和配置一起使用。

--report=<path>
    执行结果报告，输出格式为json。默认不生成。
'''

def show_usage():
    print(USAGE)
