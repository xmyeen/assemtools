# -*- coding:utf-8 -*-
#!/usr/bin/env python

import base64
from .winsvc import WIN32_APP_AGENT_SERVICE_CONTENT_DEF

WIN32_INSTALLER_CONTENT_SPLITTER_DEF = "\n#" + ">" * 100 + "\n"

WIN32_INSTALLER_CONTENT_TEMPLATE_DEF = WIN32_INSTALLER_CONTENT_SPLITTER_DEF.join([
"# -*- coding:utf-8 -*-",

'''
import site, os, sys, base64, warnings, socket, collections, zipfile, re, getopt, subprocess, shutil, pathlib
''',

f'''
# Define

CURR_SCRIPT_DIR_DEF = os.path.dirname(os.path.abspath(__file__))

PIP_INSTALL_OPTION_DEF = "{{PIP_INSTALL_OPTION_DEF}}"

APP_NAME_DEF="{{APP_NAME_DEF}}"
APP_DESCRIPTION_DEF="{{APP_DESCRIPTION_DEF}}"
APP_PROGRAM_NAME_DEF="{{APP_PROGRAM_NAME_DEF}}"
APP_WHEEL_NAME_DEF="{{APP_WHEEL_NAME}}"
APP_AGENT_NAME_DEF="{{APP_NAME_DEF}}-service-agent"
APP_AGENT_PY_DEF = {base64.b64encode(WIN32_APP_AGENT_SERVICE_CONTENT_DEF.encode('utf-8'))}
''',

'''
# Function

def show_usage():
    print('\\n'.join([
        f"{{sys.argv[0]}} [--prefix=<路径>]",
        "参数说明：",
        f"  --prefix=<Directory>            程序安装的根目录",
        f"  --win-bindir=<Directory>        指定Windows二进制目录，用于存放可执行程序或动态库；被指定的目录需要添加到环境变量。"
    ]))
    pass

def check_python(pypi_dir:str):
    print('[I]', 'This-Python', ':', sys.executable, '-', sys.version.replace('\\n', ' '))
    try:
        from pip._internal.utils.packaging import check_requires_python
        from pip._internal.utils.wheel import wheel_dist_info_dir

        name = re.sub('[A-Z]', lambda m: '_' + m.group(0).lower(), APP_NAME_DEF).strip('_')
        file_path = f"{{pypi_dir}}\\\\{{APP_WHEEL_NAME_DEF}}"

        with zipfile.ZipFile(file_path, allowZip64 = True) as z:
            info_dir = wheel_dist_info_dir(z, APP_NAME_DEF)
            metadata = dict(re.findall(r"([\\w-]*)\\:\\s*(.*)\\s*", z.read(f'{{info_dir}}/METADATA').decode()))

            python_require = metadata.get('Requires-Python')
            if python_require and not check_requires_python(python_require, sys.version_info[:3]):
                raise RuntimeError("Mismatch requiring '%s'" % (python_require or 'All'))
    except:
        exc_type, exc_value, exc_traceback_obj = sys.exc_info()
        print('[E]', 'Check-Python-Error', ':', exc_value)
        sys.exit(1)

def copy_pywin32_binaries(py_executable:str, outdir:str):
    win_bindir_path = pathlib.Path(outdir)
    if not win_bindir_path.exists(): win_bindir_path.mkdir(parents = True)

    sitepackage_string = subprocess.getoutput([py_executable, "-c", "import site; print(';'.join(site.getsitepackages()))"])
    for sitepackage in sitepackage_string.split(";"):
        sitepackage_path = pathlib.Path(sitepackage)
        for expression in "win32/PythonService.exe", "win32/*.dll", "pywin32_*/*.dll":
            for winsrv_binfile in sitepackage_path.glob(expression):
                binfile_path = win_bindir_path.joinpath(os.path.basename(winsrv_binfile))
                if not binfile_path.exists():
                    shutil.copy(winsrv_binfile, win_bindir_path)
                    print("Copy %s into %s" % (winsrv_binfile, win_bindir_path))
                else:
                    print("Find %s - Copy skipped" % (binfile_path))

def write_py(o, b64_py, **parameters):
    return o.write(base64.b64decode(b64_py).decode("utf-8").format(**parameters))
''',

'''
# Variable

Configer = collections.namedtuple("Configer", ["app_node", "app_prefix_dir", "win_bindir"])
configer = Configer(
    app_node = socket.gethostname(),
    app_prefix_dir = os.path.join(os.getenv('PROGRAMFILES'), APP_NAME_DEF),
    #win_bindir = os.path.join(os.getenv("SystemRoot"), "system32")
    win_bindir = None
)
''',

'''
# Commandline

opts, server_ids = getopt.getopt(sys.argv[1:], "he:", ["help", "prefix=", "env-source=", "win-bindir="])
for name, value in opts:
    if name in ("-h", "--help"):
        show_usage()
        sys.exit(0)
    elif name in ("--prefix"):
        configer = configer._replace(app_prefix_dir = value)
    elif name in ("--win-bindir"):
        configer = configer._replace(win_bindir = value)
''',

'''
# Middle Variable
app_dirs = binary_dir, library_dir, config_dir, data_dir, temporary_dir, backup_dir, run_dir, winexec_dir = [
    os.path.join(configer.app_prefix_dir, d) for d in ["bin", "lib", "config", "var", "tmp", "bak", "run", "Scripts"]
]

app_executable = os.path.join(winexec_dir, "python.exe")

app_win_bindir = configer.win_bindir or winexec_dir
app_winsvc_executable = os.path.join(app_win_bindir, "PythonService.exe") 

pypi_dir = os.path.join(CURR_SCRIPT_DIR_DEF, "packages")
''',

'''
# Check python
check_python(pypi_dir)
''',

'''
# Build virtual environment
if not os.path.exists(app_executable) or not os.path.samefile(sys.executable, app_executable):
    print(f"[I] Make-Virual-Enviroment : For {{configer.app_prefix_dir}}")
    os.makedirs(configer.app_prefix_dir, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", "--clear", configer.app_prefix_dir])

for d in app_dirs:
    print(f"[I] Make-Directory : For {{d}}")
    os.makedirs(d, exist_ok=True)

print(f"[I] Install-Packages : From {{pypi_dir}}")
cmdlines = [
    app_executable, 
    "-m", 
    "pip", 
    "install", 
    "-U", 
    "--force-reinstall",
    "--no-index", 
    PIP_INSTALL_OPTION_DEF,
    f"--find-links={{pypi_dir}}",
    os.path.join(pypi_dir, APP_WHEEL_NAME_DEF)
]
subprocess.run([ cl for cl in cmdlines if cl ])
''',

'''
# Make windows service
print(f"[I] Install-Win32-Service")
copy_pywin32_binaries(app_executable, app_win_bindir)
if not os.path.exists(app_winsvc_executable):
    warnings.warn("[E] Lack win32 service binaries. Please run '\\"%s\\" -m pip install pywin32' before!!!"  % (sys.executable))
    os.abort()

with open(os.path.join(winexec_dir, "%s.py" % (APP_AGENT_NAME_DEF)), "w", encoding="utf-8") as f:
    write_py(
        f, APP_AGENT_PY_DEF,
        APP_WINSVC_AGENT_NAME = APP_AGENT_NAME_DEF.title().replace("-", ""),
        APP_WINSVC_EXECUTABLE = app_winsvc_executable.replace("\\\\", "\\\\\\\\"),
        APP_DESCRIPTION = APP_DESCRIPTION_DEF,
        APP_PROGRAM_NAME = APP_PROGRAM_NAME_DEF,
        APP_ROOT = configer.app_prefix_dir.replace("\\\\", "\\\\\\\\")
    )
    print("Autogenerate %s" % (f.name))
''',

'''
# Finish
print(f"[I] End : Run '{{winexec_dir}}\\{{APP_NAME_DEF}}-*.exe' to start application")
'''
])
