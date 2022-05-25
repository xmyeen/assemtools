# -*- coding:utf-8 -*-
#!/usr/bin/env python

import os

UNIX_INSTALLER_CONTENT_TEMPLATE_DEF='''#!/bin/bash

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Define

CURR_SCRIPT_DIR_DEF="$(readlink -f $0 | xargs dirname)"

PIP_INSTALL_OPTION_DEF="{PIP_INSTALL_OPTION_DEF}"

APP_NAME_DEF="{APP_NAME_DEF}"
APP_DESCRIPTION_DEF="{APP_DESCRIPTION_DEF}"
APP_PROGRAM_NAME_DEF="{APP_PROGRAM_NAME_DEF}"
APP_WHEEL_NAME="{APP_WHEEL_NAME}"

APP_PACKAGE_DIR_DEF="$CURR_SCRIPT_DIR_DEF/packages"
APP_ADMIN_PROGRAM_NAME_DEF="app_admin"

APP_RUN_PROGRAM_COMMAND_NAME_DEF="$APP_NAME_DEF-c-run"
APP_START_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-start-on-daemon"
APP_STOP_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-stop-on-daemon"
APP_ENABLE_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-enable-on-systemd"
APP_DISABLE_DAEMON_COMMAND_NAME_DEF="$APP_NAME_DEF-c-disable-on-systemd"

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Function

function show_usage() {{
    echo "Usage"
}}

function check_python() {{
    pycmd="$1"

cat << EOF | sed -r 's/^\\s\\s\\s\\s//' | $pycmd -
    import sys, zipfile, re
    print('[I]', 'This-Python', ':', sys.executable, '-', sys.version.replace('\\n', ' '))
    try:
        from pip._internal.utils.packaging import check_requires_python, get_metadata
        from pip._internal.utils.wheel import pkg_resources_distribution_for_wheel

        name = re.sub('[A-Z]', lambda m: '_' + m.group(0).lower(), "$APP_NAME_DEF").strip('_')
        file_path = "$APP_PACKAGE_DIR_DEF/$APP_WHEEL_NAME"

        with zipfile.ZipFile(file_path, allowZip64 = True) as z:
            dist = pkg_resources_distribution_for_wheel(z, name, file_path)
            pkg_info = get_metadata(dist)
            python_require = pkg_info.get('Requires-Python')
            if python_require and not check_requires_python(python_require, sys.version_info[:3]):
                raise RuntimeError("Mismatch requiring '%s'" % (python_require or 'All'))
    except:
        exc_type, exc_value, exc_traceback_obj = sys.exc_info()
        print('[E]', 'Check-Python-Error', ':', exc_value)
        sys.exit(1)
EOF

}}

function bundle_admin(){{
    venv_dir="$1"
    node_id="$2"
    run_dir="$3"

cat << EOF | sed -r 's/^\\s\\s\\s\\s//'
    #!${{venv_dir}}/bin/python
    # -*- coding: utf-8 -*-

    import os, sys, glob, asyncio, socket, enum, re, dataclasses, typing, configparser, fcntl, getopt, time, signal, traceback

    APP_NODE_DEF = "${{node_id}}"
    APP_NAME_DEF = "${{APP_NAME_DEF}}"
    APP_PROGRAM_NAME_DEF = "${{APP_PROGRAM_NAME_DEF}}"

    RUN_DIR_DEF = "$run_dir"
    PID_FILE_DEF = f"{{RUN_DIR_DEF}}/$APP_ADMIN_PROGRAM_NAME_DEF.pid"
    CONFIG_FILE_DEF = f"{{RUN_DIR_DEF}}/$APP_ADMIN_PROGRAM_NAME_DEF.config"
    SOCK_DEF = f"{{RUN_DIR_DEF}}/$APP_ADMIN_PROGRAM_NAME_DEF.sock"

    USAGE_DEF = \'\'\'
    Usage:
        Execute program
        $ $APP_ADMIN_PROGRAM_NAME_DEF <-x|--execute> [<-c|--console>=<Console>] [<-d|--daemonize>] [PROGRAM1[ PROGRAM2...]]

        Shutdown program
        $ $APP_ADMIN_PROGRAM_NAME_DEF <-s|--shutdown> [PROGRAM1[ PROGRAM2...]]

        Restart program
        $ $APP_ADMIN_PROGRAM_NAME_DEF <-r|--restart> [<-c|--console>=<Console>] [PROGRAM1[ PROGRAM2...]]

        Redirect application console output
        $ $APP_ADMIN_PROGRAM_NAME_DEF <--redirect> [<-c|--console>=<Console>]

    Parameter:
        Console     Ex: /dev/null, app.out, localhost:3000, 127.0.0.1:3000
    \'\'\'

    class MainCmdDef(enum.Enum):
        ADMIN = 1
        CONSOLE = 2

        def make_command(self, *content:str) -> str:
            return ' '.join([self.name, *content])

        def yes(self, cmd:str) -> bool:
            return self.name == cmd

    class AdminCmdDef(enum.Enum):
        EXECUTABLE = 1
        SHUTDOWN = 2
        RESTART = 3
        REDIRECT = 4

        def yes(self, cmd:str) -> bool:
            return self.name == cmd

    @dataclasses.dataclass
    class Config(object):
        node_id: str = dataclasses.field(default_factory = lambda : socket.gethostname())

        def load() -> 'Config':
            config = Config()

            # 读取配置库
            if os.path.exists(CONFIG_FILE_DEF):
                cf = configparser.ConfigParser()
                config.node_id = cf.get("node", "node_id")

            return config

    class AppAdminister(object):
        def __init__(self):
            self.__app_console = None
            self.__app_program_name_set = set(APP_PROGRAM_NAME_DEF.split(' '))

        def __aiter__(self) -> 'AppAdminister':
            return self

        async def __anext__(self):
            try:
                await self.syn_program()
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                raise StopAsyncIteration

        def get_application_program_name_set(self) -> typing.Set[str]: return self.__app_program_name_set
        def set_application_program_name_set(self, names:typing.Iterable[str]): self.__app_program_name_set =  set([n for n in names])
        app_program_name_set = property(get_application_program_name_set, set_application_program_name_set, None, 'Application Program Name Set')

        def get_application_console(self) -> str: return self.__app_console or '/dev/null'
        def set_applicaiton_console(self, console:str): self.__app_console =  re.sub(r'^([\\\\d\\\\w\\\\.]+)\\\\:(\\\\d+)$', '/dev/tcp/\\\\\\\\1/\\\\\\\\2', console.strip()) if console else None
        app_console = property(get_application_console, set_applicaiton_console, None, 'Application Console Output')

        def scan_program_status(self) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
            program_status_info = {{ name : [] for name in APP_PROGRAM_NAME_DEF.split(",") }}

            for exe in glob.glob('/proc/*/exe'):
                try:
                    if not os.path.samefile(sys.executable, exe): continue

                    _, _, pid, _ = exe.split('/')
                    if pid == os.getpid(): continue

                    py_cmdline = [ s for s in open(f'/proc/{{pid}}/cmdline', 'r').read().strip().split('\\\\x00') if not s.startswith('-') ]
                    if 1 >= len(py_cmdline): continue

                    program_file = py_cmdline[1] if os.path.isabs(py_cmdline[1]) else os.path.join(f'/proc/{{pid}}/cwd', py_cmdline[1])
                    if not os.path.samefile(os.path.dirname(program_file), os.path.join(sys.prefix, 'bin')): continue

                    program_name = os.path.basename(program_file)
                    if program_name not in program_status_info: continue

                    with open(f'/proc/{{pid}}/status') as status:
                        while line := status.readline():
                            k,v = line.strip().split(':')
                            program_status_info[program_name].append({{ k.strip().lower() : v.strip() }})
                except FileNotFoundError:
                    pass
                except BaseException as e:
                    print(e, type(e))

            return program_status_info

        async def restart_program(self, *app_programs:str, **cfg:typing.Any):
            if cfg.get('console'): self.app_console = cfg.get('console')

            target_programs = app_programs if app_programs else APP_PROGRAM_NAME_DEF.split(",")

            app_status_info = self.scan_program_status()
            for app_program_name, app_program_statuses in app_status_info.items():
                if app_program_statuses and (app_program_name in target_programs):
                    # 进程正在执行，且属于需要重启的进程，则需要杀死该进程
                    for app_program_status in app_program_statuses:
                        if pid := app_program_status.get('pid'):
                            os.kill(int(pid), 9)

        async def start_program(self, *app_programs:str, **cfg:typing.Any):
            self.app_console = cfg.get('console')
            self.app_program_name_set.update(app_programs or APP_PROGRAM_NAME_DEF.split(","))

        async def stop_program(self, *app_programs:str, **cfg:typing.Any):
            self.app_program_name_set.difference_update(app_programs or APP_PROGRAM_NAME_DEF.split(","))

            app_status_info = self.scan_program_status()
            for app_program_name, app_program_statuses in app_status_info.items():
                if app_program_statuses and (app_program_name not in self.app_program_name_set):
                    # 进程正在执行，但是属于需要忽略的程序，则需要杀死该进程
                    for app_program_status in app_program_statuses:
                        if pid := app_program_status.get('pid'):
                            os.kill(int(pid), 9)

        async def redirect_program(self, console:str = None):
            await self.restart_program(console = console)

        async def syn_program(self):
            app_env = os.environ.copy()
            app_status_info = self.scan_program_status()
            # config = Config.load()

            for app_program_name, app_program_statuses in app_status_info.items():
                if app_program_statuses and (app_program_name not in self.app_program_name_set):
                    # 进程正在执行，但是属于需要忽略的程序，则需要杀死该进程
                    for app_program_status in app_program_statuses:
                        if pid := app_program_status.get('pid'):
                            os.kill(int(pid), 9)

                if not app_program_statuses and (app_program_name in self.app_program_name_set):
                    # 进程未执行，且不是需要忽略的程序，则需要启动该程序
                    if self.app_console.startswith('/dev/tcp') or self.app_console.startswith('/dev/udp'):
                        cmdline = '\\\\n'.join([
                            f"exec 3>{{self.app_console}}",
                            f"echo \\\\"{{MainCmdDef.CONSOLE.make_command(APP_NODE_DEF, APP_NAME_DEF, app_program_name)}}\\\\" >&3",
                            f"exec {{sys.executable}} -u bin/{{app_program_name}} >&3 2>&3 &"
                            # "exec 3>&-"
                        ])
                    elif self.app_console != '/dev/null':
                        cmdline = f"{{sys.executable}} -u bin/{{app_program_name}} >{{self.app_console}} 2>&1 &"
                    else:
                        cmdline = f"{{sys.executable}} bin/{{app_program_name}} >/dev/null 2>&1 &"

                    print('Run program:', cmdline)

                    p = await asyncio.create_subprocess_shell(cmdline, executable='/bin/bash', cwd = sys.prefix, env = app_env, shell = True)
                    await p.wait()

        async def handle_client(self, reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
            async for rawdata in reader:
                print('Request: ', rawdata)

                cmd, *cmd_args = rawdata.decode('utf-8').strip().split(' ')
                if MainCmdDef.ADMIN.yes(cmd):
                    await self.administer(*cmd_args)

        async def administer(self, *admin_args:str):
            setting, *app_programs = parse_command_arguments(*admin_args)
            command = setting.get('command')

            print('Administer:', command, setting)

            if AdminCmdDef.EXECUTABLE.yes(command):
                await self.start_program(*app_programs, **setting)

            if AdminCmdDef.SHUTDOWN.yes(command):
                await self.stop_program(*app_programs, **setting)

            if AdminCmdDef.RESTART.yes(command):
                await self.restart_program(*app_programs, **setting)

            if AdminCmdDef.REDIRECT.yes(command):
                await self.redirect_program(setting.get('console'))

        async def serve(self, *app_programs:str, **cfg:typing.Any):
            print("Run server as daemon")

            self.app_program_name_set = app_programs or APP_PROGRAM_NAME_DEF.split(' ')
            self.app_console = cfg.get('console')

            asyncio.create_task(asyncio.start_unix_server(self.handle_client, SOCK_DEF))
            async for _ in self:
                pass

    def parse_command_arguments(*cmd_args):
        setting = {{}}
        opts, args = getopt.getopt(cmd_args,'hxsrc:d', ['help', 'execute', 'shutdown', 'restart', 'redirect', 'daemonize', 'console='])
        for opt,val in opts:
            if opt in ('-h','--help'):
                print(USAGE_DEF)
                sys.exit(0)
            if opt in ('-x', '--execute'):
                setting.update(command = AdminCmdDef.EXECUTABLE.name)
            if opt in ('-s', '--shutdown'):
                setting.update(command = AdminCmdDef.SHUTDOWN.name)
            if opt in ('-r', '--restart'):
                setting.update(command = AdminCmdDef.RESTART.name)
            if opt in ('--redirect', ):
                setting.update(command = AdminCmdDef.REDIRECT.name)
            if opt in ('-c', '--console'):
                setting.update(console = val)
            if opt in ('-d', '--daemonize'):
                setting.update(daemonize = True)

        return [setting, *args]

    def do_client_request():
        print('Do client request')
        with socket.socket(socket.AF_UNIX) as sock:
            for _ in range(5):
                try:
                    sock.connect(SOCK_DEF)
                    sock.send(MainCmdDef.ADMIN.make_command(*sys.argv[1:]).encode('utf-8'))
                except (ConnectionError, FileNotFoundError):
                    time.sleep(1)
                else:
                    break

    def main():
        pidfd = os.open(PID_FILE_DEF, os.O_CREAT | os.O_WRONLY )

        try:
            #It will unlock file after closing fd. No need to set LOCK_UN.
            fcntl.flock(pidfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Run as client")
            os.close(pidfd)
            do_client_request()
            sys.exit(0)

        try:
            setting, *app_programs = parse_command_arguments(*sys.argv[1:])

            if setting.get('daemonize'):
                if 0 < os.fork():
                    do_client_request()
                    sys.exit(0)

                #os.chdir('/')
                os.umask(0)
                os.setsid()

                if 0 < os.fork():
                    sys.exit(0)

                for fd in sys.stdin, sys.stdout, sys.stderr:
                    fd.flush()
                    # fd.close()

                f0 = open(f'/dev/null', 'w+')
                os.dup2(f0.fileno(), sys.stdout.fileno())

                f1 = open(f'{{RUN_DIR_DEF}}/error.log', 'w+')
                os.dup2(f1.fileno(), sys.stderr.fileno())

                f2 = open('/dev/null', 'r')
                os.dup2(f2.fileno(), sys.stdin.fileno())

                signal.signal(signal.SIGCHLD, signal.SIG_DFL)
            else:
                if 0 == os.fork():
                    do_client_request()
                    sys.exit(0)

            pidfo = os.fdopen(pidfd, 'w')
            pidfo.write("%d" % (os.getpid()))
            pidfo.flush()
            #pidfo.close()

            admin = AppAdminister()
            asyncio.run(admin.serve(*app_programs, **setting))
        finally:
            os.close(pidfd)

    if __name__ == '__main__':
        if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
            print(USAGE_DEF)
            sys.exit(0)

        if not os.path.exists(RUN_DIR_DEF):
            os.makedirs(RUN_DIR_DEF)

        try:
            main()
        except (SystemExit, KeyboardInterrupt):
            pass
EOF
}}

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Variable

APP_NODE=`hostname`
RUN_MODE=""
BASE_PY_CMD=""
ENV_SOURCE=""
APP_PREFIX_DIR="/usr/local/lib/$APP_NAME_DEF"

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

## Get programs
#for arg in $@
#do
#    APP_PROGRAM="$arg $APP_PROGRAM"
#done

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

# Check python
# type $py_cmd >/dev/null 2>&1 || {{ echo "Unavailable $py_cmd - Abort!" && exit 1; }}
echo "[I] Use-Python : $BASE_PY_CMD - `$BASE_PY_CMD --version`"

# Write environment file
cat <<EOF >$env_source_file
for e in $ENV_SOURCE; do [ -n "\$e" ] && source \$e; done
export PATH=$binary_dir:\$PATH
export LD_LIBRARY_PATH=$library_dir:`$py_cmd -c 'import sys;print(sys.base_prefix)'`/lib:\$LD_LIBRARY_PATH
EOF

echo "[I] Make-Directories : For $APP_PREFIX_DIR"
mkdir -p $binary_dir $library_dir $config_dir $data_dir $temporary_dir $backup_dir $run_dir

echo "[I] Install-Packages : From $APP_PACKAGE_DIR_DEF"
$py_cmd -m pip install -U --force-reinstall --no-index $PIP_INSTALL_OPTION_DEF --find-links=$APP_PACKAGE_DIR_DEF $APP_PACKAGE_DIR_DEF/$APP_WHEEL_NAME

# Install admin
echo "[I] Install-Admin : To $admin_program_file"
bundle_admin $APP_PREFIX_DIR $APP_NODE $run_dir > $admin_program_file
chmod +x $admin_program_file

# Install scripts
echo "[I] Install-Scripts : To $binary_dir"
cat <<EOF >$binary_dir/$APP_RUN_PROGRAM_COMMAND_NAME_DEF
#!/bin/bash
source $env_source_file
cd $APP_PREFIX_DIR
exec bin/\$1
EOF

cat <<EOF >$binary_dir/$APP_START_DAEMON_COMMAND_NAME_DEF
#!/bin/bash
echo "Start $APP_NAME_DEF"
$admin_program_file -x -d
EOF

cat <<EOF >$binary_dir/$APP_STOP_DAEMON_COMMAND_NAME_DEF
#!/bin/bash
echo "Stop $APP_NAME_DEF"
$admin_program_file -s
sleep 1
cat $run_dir/*.pid | xargs kill -9
rm -rf $run_dir/*
EOF

cat <<EOF >$binary_dir/$APP_ENABLE_DAEMON_COMMAND_NAME_DEF
#!/bin/bash

if [ "active" != "\\$(systemctl is-active sysinit.target)" ]
then
    echo "Systemd service is inactive (dead). Please recover it!"
    exit 1
fi

for name in $APP_PROGRAM_NAME_DEF
do
    srv="\\${{name}}d.service"

(
cat << __EOF__ | sed -r 's/^\\s\\s\\s\\s//'
    [Unit]
    Description=$APP_DESCRIPTION_DEF
    Documentation=
    After=network.target
    Wants=
    StartLimitInterval=0

    [Service]
    Environment="APP_ENV=prod"
    WorkingDirectory=$APP_PREFIX_DIR
    ExecStart=$APP_PREFIX_DIR/bin/$APP_RUN_PROGRAM_COMMAND_NAME_DEF \\${{name}}
    ExecReload=/bin/kill -HUP \\\\\\$MAINPID
    TimeoutStopSec=30s
    TimeoutStartSec=30s
    Type=simple
    KillMode=mixed
    Restart=always
    RestartSec=20s
__EOF__
) > /usr/lib/systemd/system/\\$srv

    systemctl enable \\$srv

    if [ "active" != "\\$(systemctl is-active \\$srv)" ]
    then
        systemctl start \\$srv
    fi
done

EOF

cat <<EOF >$binary_dir/$APP_DISABLE_DAEMON_COMMAND_NAME_DEF
#!/bin/bash

if [ "active" != "\\$(systemctl is-active sysinit.target)" ]
then
    echo "Systemd service is inactive (dead). Please recover it!"
    exit 1
fi

for name in $APP_PROGRAM_NAME_DEF
do
    srv="\\${{name}}d.service"

    if [ "0" == "\\$(systemctl list-units --no-legend --no-pager \\$srv | wc -l)" ]
    then
        echo "No '\\$srv' - Skip it"
        continue
    fi

    if [ "active" == "\\$(systemctl is-active \\$srv)" ]
    then
        echo "Stop \\$srv"
        systemctl stop \\$srv
    fi

    sleep 3

    if [ "active" == "\\$(systemctl is-active \\$srv)" ]
    then
        echo "kill \\$srv"
        systemctl kill \\$srv
    fi

    systemctl disable \\$srv
    find /usr/lib/systemd/ /lib/systemd/ /etc/systemd/ -name "\\$srv" -exec rm -f {{}} \;
done

systemctl daemon-reload
systemctl reset-failed 
EOF

find $binary_dir -iname "$APP_NAME_DEF*" -exec chmod 777 {{}} \;

echo "[I] End : Run '$binary_dir/$APP_NAME_DEF-c-*' scripts to start application"
'''


WIN32_INSTALLER_CONTENT_TEMPLATE_DEF = '''# -*- coding:utf-8 -*-

import os, sys, warnings, socket, collections, zipfile, re, getopt, subprocess

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Define

CURR_SCRIPT_DIR_DEF = os.path.dirname(os.path.abspath(__file__))

PIP_INSTALL_OPTION_DEF = "{PIP_INSTALL_OPTION_DEF}"

APP_NAME_DEF="{APP_NAME_DEF}"
APP_DESCRIPTION_DEF="{APP_DESCRIPTION_DEF}"
APP_PROGRAM_NAME_DEF="{APP_PROGRAM_NAME_DEF}"
APP_WHEEL_NAME="{APP_WHEEL_NAME}"

APP_PACKAGE_DIR_DEF=f"{{CURR_SCRIPT_DIR_DEF}}\\\\packages"

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Function

def show_usage():
    print('\\n'.join([
        f"{{sys.argv[0]}} [--prefix=<路径>]",
        "参数说明：",
        f"  --prefix             安装程序的根路径"
    ]))
    pass


def check_python():
    print('[I]', 'This-Python', ':', sys.executable, '-', sys.version.replace('\\n', ' '))
    try:
        from pip._internal.utils.packaging import check_requires_python
        from pip._internal.utils.wheel import wheel_dist_info_dir

        name = re.sub('[A-Z]', lambda m: '_' + m.group(0).lower(), APP_NAME_DEF).strip('_')
        file_path = f"{{APP_PACKAGE_DIR_DEF}}\\\\{{APP_WHEEL_NAME}}"

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

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Variable

Configer = collections.namedtuple("Configer", ["app_node", "app_prefix_dir"])
configer = Configer(
    app_node = socket.gethostname(),
    app_prefix_dir = os.path.join(os.getenv('PROGRAMFILES'), APP_NAME_DEF)
)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Commandline

opts, server_ids = getopt.getopt(sys.argv[1:], "he:", ["help", "prefix=", "env-source=" ])
for name, value in opts:
    if name in ("-h", "--help"):
        show_usage()
        sys.exit(0)
    elif name in ("--prefix"):
        configer = configer._replace(app_prefix_dir = value)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# Middle Variable
binary_dir = os.path.join(configer.app_prefix_dir, "bin")
library_dir = os.path.join(configer.app_prefix_dir, "lib")
config_dir = os.path.join(configer.app_prefix_dir, "config")
data_dir = os.path.join(configer.app_prefix_dir, "var")
temporary_dir = os.path.join(configer.app_prefix_dir, "tmp")
backup_dir = os.path.join(configer.app_prefix_dir, "bak")
run_dir = os.path.join(configer.app_prefix_dir, "run")

# Check python
check_python()

# Build virtual environment
app_executable = os.path.join(configer.app_prefix_dir, "Scripts", "python.exe")
if not os.path.exists(app_executable) or not os.path.samefile(sys.executable, app_executable):
    print(f"[I] Make-Virual-Enviroment : For {{configer.app_prefix_dir}}")
    os.makedirs(configer.app_prefix_dir, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", "--clear", configer.app_prefix_dir])

for d in binary_dir, library_dir, config_dir, data_dir, temporary_dir, backup_dir, run_dir:
    print(f"[I] Make-Directory : For {{d}}")
    os.makedirs(d, exist_ok=True)

print(f"[I] Install-Packages : From {{APP_PACKAGE_DIR_DEF}}")
cmdlines = [
    app_executable, 
    "-m", 
    "pip", 
    "install", 
    "-U", 
    "--force-reinstall",
    "--no-index", 
    PIP_INSTALL_OPTION_DEF,
    f"--find-links={{APP_PACKAGE_DIR_DEF}}",
    os.path.join(APP_PACKAGE_DIR_DEF, APP_WHEEL_NAME)
]
subprocess.run([ cl for cl in cmdlines if cl ])

print(f"[I] End : Run '{{binary_dir}}\\{{APP_NAME_DEF}}-*' scripts to start application")
'''


INSTALLER_CONTENT_TEMPLATE_DEF = WIN32_INSTALLER_CONTENT_TEMPLATE_DEF if 'nt' == os.name else UNIX_INSTALLER_CONTENT_TEMPLATE_DEF