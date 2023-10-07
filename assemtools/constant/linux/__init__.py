#!/usr/bin/env python
# -*- coding:utf-8 -*-

from .app_admin import LINUX_APP_ADMIN_CONTENT_DEF
from .app_systemd_daemon import APP_START_DAEMON_COMMAND_CONTENT_DEF, APP_STOP_DAEMON_COMMAND_CONTENT_DEF, APP_ENABLE_DAEMON_COMMAND_CONTENT_DEF, APP_DISABLE_DAEMON_COMMAND_CONTENT_DEF

LINUX_INSTALLER_CONTENT_TEMPLATE_DEF = "\n".join([
"#!/bin/bash",

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Define

CURR_SCRIPT_DIR_DEF="$(readlink -f $0 | xargs dirname)"

PIP_INSTALL_OPTION_DEF="{PIP_INSTALL_OPTION_DEF}"

APP_NAME_DEF="{APP_NAME_DEF}"
APP_DESCRIPTION_DEF="{APP_DESCRIPTION_DEF}"
APP_PROGRAM_NAME_DEF="{APP_PROGRAM_NAME_DEF}"
APP_WHEEL_NAME="{APP_WHEEL_NAME}"

APP_PYPI_DIR="$CURR_SCRIPT_DIR_DEF/packages"
APP_ADMIN_PROGRAM_NAME_DEF="{APP_ADMIN_PROGRAM_NAME_DEF}"

APP_RUN_PROGRAM_COMMAND_NAME_DEF="$APP_NAME_DEF-c-run"
APP_START_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-start-on-daemon"
APP_STOP_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-stop-on-daemon"
APP_ENABLE_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-enable-on-systemd"
APP_DISABLE_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-disable-on-systemd"
''',

f'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Function

function show_usage() {{{{
    echo "Usage"
}}}}

function check_python() {{{{
    pycmd="$1"

cat << EOF | sed -r 's/^\\s\\s\\s\\s//' | $pycmd -
    import sys, zipfile, re
    print('[I]', 'This-Python', ':', sys.executable, '-', sys.version.replace('\\n', ' '))
    try:
        from pip._internal.utils.packaging import check_requires_python

        file_path = "$APP_PYPI_DIR/$APP_WHEEL_NAME"
        name = re.sub('[A-Z]', lambda m: '_' + m.group(0).lower(), "$APP_NAME_DEF").strip('_')
        wheel_python_requrire = None

        with zipfile.ZipFile(file_path, allowZip64 = True) as z:
            for file_data in z.infolist():
                if not file_data.filename.endswith(".dist-info/METADATA"): continue

                with z.open(file_data.filename, 'r') as f:
                    for line_content in f.read().decode('utf-8').splitlines():
                        splits = line_content.strip().split(":")
                        if 2 > len(splits): continue
                        if not splits[0].strip().startswith("Requires-Python"): continue
                        wheel_python_requrire = splits[1].strip()
                        break
                break
        if wheel_python_requrire and not check_requires_python(wheel_python_requrire, sys.version_info[:3]):
            raise RuntimeError("Mismatch requiring '%s'" % (wheel_python_requrire or 'All'))
    except:
        exc_type, exc_value, exc_traceback_obj = sys.exc_info()
        print('[E]', 'Check-Python-Error', ':', exc_value)
        sys.exit(1)
EOF
}}}}

function bundle_admin(){{{{
    venv_dir="$1"
    node_id="$2"
    run_dir="$3"

#cat << EOF | sed -r 's/^\\s\\s\\s\\s//'
cat << EOF
{LINUX_APP_ADMIN_CONTENT_DEF}
EOF
}}}}
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Variable

APP_NODE=`hostname`
RUN_MODE=""
BASE_PY_CMD=""
ENV_SOURCE=""
APP_PREFIX_DIR="/usr/local/lib/$APP_NAME_DEF"
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Commandline

OPTIONS=$(getopt -o he:p:n: -al help,prefix:,env-source:,python:,node: -n "$0 -h" -s sh -- "$@")
eval set -- "$OPTIONS"
while [ -n "$1" ]
do
    case "$1" in
        -h|--help)
            show_usage
            shift;exit 0
        ;;
        --prefix)
            APP_PREFIX_DIR="$2"
            shift 2
        ;;
        -e,--env-source)
            ENV_SOURCE="$2 $ENV_SOURCE"
            shift 2
        ;;
        -p|--python)
            BASE_PY_CMD="$2"
            shift 2
        ;;
        -n|--node)
            APP_NODE="$2"
            shift 2
        ;;
        --)
            shift
            break
        ;;
        *)
            echo "[E] Command-Line-Error : Internal Error!"
            exit 1
        ;;
    esac
done
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# Middle Variable
binary_dir="$APP_PREFIX_DIR/bin"
library_dir="$APP_PREFIX_DIR/lib"
config_dir="$APP_PREFIX_DIR/config"
data_dir="$APP_PREFIX_DIR/var"
temporary_dir="$APP_PREFIX_DIR/tmp"
backup_dir="$APP_PREFIX_DIR/bak"
run_dir="$APP_PREFIX_DIR/run"

py_cmd="$binary_dir/python"
env_source_file="$APP_PREFIX_DIR/env"
venv_cfg_file="$APP_PREFIX_DIR/pyvenv.cfg"
admin_program_file="$binary_dir/$APP_ADMIN_PROGRAM_NAME_DEF"
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Build or reuse virtual environment
if [ ! -e $venv_cfg_file ]||[ ! -e $py_cmd ]||[ "$APP_PREFIX_DIR" != `$py_cmd -c 'import sys;print(sys.prefix)'` ]
then
    # Find python
    if  [ -z "$BASE_PY_CMD" ]
    then
        for base_py_cmd in $(find /usr/bin /usr/local/bin /opt -maxdepth 5 -path "*/bin/python3")
        do
            check_python $base_py_cmd && 
            BASE_PY_CMD=$base_py_cmd &&
            break
        done 
    fi

    if [ -z "$BASE_PY_CMD" ]
    then
        echo "[E] Python-Not-Found : No python command available - Abort"
        exit 1
    fi

    $BASE_PY_CMD -m venv --clear $APP_PREFIX_DIR
else
    BASE_PY_CMD="`$py_cmd -c 'import sys; print(sys.base_prefix)'`/bin/python3"
fi
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Check python
# type $py_cmd >/dev/null 2>&1 || {{ echo "Unavailable $py_cmd - Abort!" && exit 1; }}
echo "[I] Use-Python : $BASE_PY_CMD - `$BASE_PY_CMD --version`"
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Write environment file
cat <<EOF >$env_source_file
for e in $ENV_SOURCE; do [ -n "\\$e" ] && source \\$e; done
export PATH=$binary_dir:\\$PATH
export LD_LIBRARY_PATH=$library_dir:`$py_cmd -c 'import sys;print(sys.base_prefix)'`/lib:\\$LD_LIBRARY_PATH
EOF
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
echo "[I] Make-Directories : For $APP_PREFIX_DIR"
mkdir -p $binary_dir $library_dir $config_dir $data_dir $temporary_dir $backup_dir $run_dir
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
echo "[I] Install-Packages : From $APP_PYPI_DIR"
$py_cmd -m pip install -U --force-reinstall --no-index $PIP_INSTALL_OPTION_DEF --find-links=$APP_PYPI_DIR $APP_PYPI_DIR/$APP_WHEEL_NAME
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Install admin
echo "[I] Install-Admin : To $admin_program_file"
bundle_admin $APP_PREFIX_DIR $APP_NODE $run_dir > $admin_program_file
chmod +x $admin_program_file
''',

f'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Install scripts
echo "[I] Install-Scripts : To $binary_dir"
cat <<EOF >$binary_dir/$APP_RUN_PROGRAM_COMMAND_NAME_DEF
#!/bin/bash
source $env_source_file
cd $APP_PREFIX_DIR
exec bin/\\$1
EOF

cat <<EOF >$binary_dir/$APP_START_DAEMON_COMMAND_NAME_DEF
{APP_START_DAEMON_COMMAND_CONTENT_DEF}
EOF

cat <<EOF >$binary_dir/$APP_STOP_DAEMON_COMMAND_NAME_DEF
{APP_STOP_DAEMON_COMMAND_CONTENT_DEF}
EOF

cat <<EOF >$binary_dir/$APP_ENABLE_DAEMON_COMMAND_NAME_DEF
{APP_ENABLE_DAEMON_COMMAND_CONTENT_DEF}
EOF

cat <<EOF >$binary_dir/$APP_DISABLE_DAEMON_COMMAND_NAME_DEF
{APP_DISABLE_DAEMON_COMMAND_CONTENT_DEF}
EOF
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
find $binary_dir -iname "$APP_NAME_DEF*" -exec chmod 777 {{}} \\;
''',

'''
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
echo "[I] End : Run '$binary_dir/$APP_NAME_DEF-c-*' scripts to start application"
'''
])