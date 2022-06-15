# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os,sys,subprocess,json,warnings

USAGE = f'''
命名: python -m assemtools.executable.jupyter [OPTION]...
Help for assemtools

选项:
-h,--help                      命令使用说明
'''

def main():
    try:
        import ipykernal
    except BaseException as e:
        warnings.warn("Import ipykernal failed - Please install or repair it - " + str(e))
        sys.exit(1)

    try:
        subprocess.run('jupyter --version', shell = True)
    except BaseException as e:
        warnings.warn("Not found jupyter - Please install or repair it - " + str(e))
        sys.exit(1)

    try:
        kernelspec_cfgs = json.loads(subprocess.getoutput("jupyter kernelspec list --json"))
        for _, py_cfg in kernelspec_cfgs.get('kernelspecs').items():
            pycmd = py_cfg.get('spec').get('argv')[0]
            pycmd_path = subprocess.getoutput(f'{pycmd} -c "import sys;print(sys.executable)"')
            if os.path.isfile(pycmd_path) and os.path.samefile(pycmd_path, sys.executable):
                break 
        else:
            kernal_name = os.path.basename(sys.prefix)
            subprocess.run(f"{sys.executable} -m ipykernel install --name {kernal_name}")

        envs = os.environ.copy()
        envs.update(
            PYTHONPATH = os.pathsep.join([
                subprocess.getoutput("pipenv --where"),
                envs.get("PYTHONPATH", "")
            ]),
            APP_ENV = "dev"
        )
        cmd = ' '.join(["jupyter", "notebook"] + sys.argv[1:])
        sys.exit(subprocess.run(cmd, env=envs, shell=True))
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        warnings.warn(str(e))
        sys.exit(1)

if '__main__' == __name__:
    main()