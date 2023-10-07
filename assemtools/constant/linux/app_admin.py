#!/usr/bin/env python
# -*- coding:utf-8 -*-

LINUX_APP_ADMIN_CONTENT_DEF = '''#!${{venv_dir}}/bin/python
# -*- coding: utf-8 -*-

import os, sys, glob, threading, asyncio, socket, enum, re, dataclasses, typing, configparser, fcntl, getopt, time, signal, traceback

APP_NODE_DEF = os.getenv("APP_NODE", "${{node_id}}")
APP_NAME_DEF = "${{APP_NAME_DEF}}"
APP_PROGRAM_NAME_DEF = "${{APP_PROGRAM_NAME_DEF}}"

RUN_DIR_DEF = "$run_dir"
PID_FILE_DEF = f"{{RUN_DIR_DEF}}/$APP_ADMIN_PROGRAM_NAME_DEF.pid"
CONFIG_FILE_DEF = f"{{RUN_DIR_DEF}}/$APP_ADMIN_PROGRAM_NAME_DEF.config"
SOCK_DEF = f"{{RUN_DIR_DEF}}/$APP_ADMIN_PROGRAM_NAME_DEF.sock"

USAGE_DEF = \'\'\'
Usage:
    Run admin program
    $ $APP_ADMIN_PROGRAM_NAME_DEF [<-d|--daemonize>] [--without=<feature>] [PROGRAM1[ PROGRAM2...]]

    Execute program
    $ $APP_ADMIN_PROGRAM_NAME_DEF <-x|--execute> [<-c|--console>=<Console>] [PROGRAM1[ PROGRAM2...]]

    Shutdown program
    $ $APP_ADMIN_PROGRAM_NAME_DEF <-s|--shutdown> [PROGRAM1[ PROGRAM2...]]

    Restart program
    $ $APP_ADMIN_PROGRAM_NAME_DEF <-r|--restart> [<-c|--console>=<Console>] [PROGRAM1[ PROGRAM2...]]

    Redirect application console output
    $ $APP_ADMIN_PROGRAM_NAME_DEF <--redirect> [<-c|--console>=<Console>]

Parameter:
    Feature     BACKGROUND_APP_PROCESS
    Console     Ex: /dev/null, app.out, localhost:3000, 127.0.0.1:3000
\'\'\'

class MainCmdDef(enum.Enum):
    ADMIN = 1
    CONSOLE = 2

    def make_command(self, *content:str) -> str:
        return ' '.join([self.name, *content])

    def yes(self, cmd:str) -> bool:
        return self.name == cmd

class AdminFeatureDef(enum.Enum):
    BACKGROUND_APP_PROCESS = 1


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
    def __init__(self,  *app_programs:str, **app_cfg:typing.Any):
        self.__app_program_name_set = set(app_programs or APP_PROGRAM_NAME_DEF.split(' '))
        self.__app_cfg = app_cfg

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            await self.syn_program()
            await asyncio.sleep(1)
        except (SystemExit, KeyboardInterrupt) as e:
            raise StopAsyncIteration

    def get_application_program_name_set(self) -> typing.Set[str]: return self.__app_program_name_set
    app_program_name_set = property(get_application_program_name_set, None, None, 'Application Program Name Set')

    def get_application_console(self) -> str:
        if console := self.__app_cfg.get('console'):
            return re.sub(r'^([\\\\d\\\\w\\\\.]+)\\\\:(\\\\d+)$', '/dev/tcp/\\\\\\\\1/\\\\\\\\2', console.strip())
        else:
            return '/dev/null'
    app_console = property(get_application_console, None, None, 'Application Console Output')

    def has_feature(self, feature: str) -> bool:
        return feature in self.__app_cfg.get('features')

    def scan_program_status(self) -> dict[str, dict[str, typing.Any]]:
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
            except (FileNotFoundError, PermissionError):
                pass
            except (SystemExit, KeyboardInterrupt) as e:
                raise e
            except BaseException as e:
                print(e, type(e))

        return program_status_info

    async def restart_program(self, *app_programs:str):
        target_programs = app_programs if app_programs else APP_PROGRAM_NAME_DEF.split(",")

        app_status_info = self.scan_program_status()
        for app_program_name, app_program_statuses in app_status_info.items():
            if app_program_statuses and (app_program_name in target_programs):
                # 进程正在执行，且属于需要重启的进程，则需要杀死该进程
                for app_program_status in app_program_statuses:
                    if pid := app_program_status.get('pid'):
                        os.kill(int(pid), 9)

    async def start_program(self, *app_programs:str):
        self.app_program_name_set.update(app_programs or APP_PROGRAM_NAME_DEF.split(","))

    async def stop_program(self, *app_programs:str):
        self.app_program_name_set.difference_update(app_programs or APP_PROGRAM_NAME_DEF.split(","))

        app_status_info = self.scan_program_status()
        for app_program_name, app_program_statuses in app_status_info.items():
            if app_program_statuses and (app_program_name not in self.app_program_name_set):
                # 进程正在执行，但是属于需要忽略的程序，则需要杀死该进程
                for app_program_status in app_program_statuses:
                    if pid := app_program_status.get('pid'):
                        os.kill(int(pid), 9)

    async def redirect_program(self, console:str = None):
        self.__app_cfg.update(dict(console = console))
        await self.restart_program()

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
                bg_token = ' &' if self.has_feature(AdminFeatureDef.BACKGROUND_APP_PROCESS.name) else ''
                # 进程未执行，且不是需要忽略的程序，则需要启动该程序
                if self.app_console.startswith('/dev/tcp') or self.app_console.startswith('/dev/udp'):
                    cmdline = '\\\\n'.join([
                        f"exec 3>{{self.app_console}}",
                        f"echo \\\\"{{MainCmdDef.CONSOLE.make_command(APP_NODE_DEF, APP_NAME_DEF, app_program_name)}}\\\\" >&3",
                        f"exec {{sys.executable}} -u bin/{{app_program_name}} >&3 2>&3{{bg_token}}"
                        # "exec 3>&-"
                    ])
                elif self.app_console != '/dev/null':
                    cmdline = f"exec {{sys.executable}} -u bin/{{app_program_name}} >{{self.app_console}} 2>&1{{bg_token}}"
                else:
                    cmdline = f"exec {{sys.executable}} bin/{{app_program_name}} >/dev/null 2>&1{{bg_token}}"

                print('Run program:', cmdline)

                await asyncio.create_subprocess_shell(cmdline, executable='/bin/bash', cwd = sys.prefix, env = app_env, shell = True)

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
            await self.start_program(*app_programs)

        if AdminCmdDef.SHUTDOWN.yes(command):
            await self.stop_program(*app_programs)

        if AdminCmdDef.RESTART.yes(command):
            await self.restart_program(*app_programs)

        if AdminCmdDef.REDIRECT.yes(command):
            await self.redirect_program(setting.get('console'))

    async def serve(self):
        print("Start service")

        asyncio.create_task(asyncio.start_unix_server(self.handle_client, SOCK_DEF))
        try:
            async for _ in self:
                try:
                    # Avoiding zombie processes, such as Docker
                    os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    pass
        finally:
            # Kill all child processes
            for app_program_name, app_program_statuses in self.scan_program_status().items():
                for app_program_status in app_program_statuses:
                    if os.getpid() != app_program_status.get('ppid'):
                        continue
                    if pid := app_program_status.get('pid'):
                        os.kill(int(pid), 9)

def parse_command_arguments(*cmd_args):
    setting = {{ "features" : list(AdminFeatureDef.__members__.keys()) }}
    opts, args = getopt.getopt(cmd_args,'hxsrc:d', ['help', 'execute', 'shutdown', 'restart', 'redirect', 'daemonize', 'console=', 'without='])
    for opt,val in opts:
        if opt in ('-h','--help'):
            print(USAGE_DEF)
            sys.exit(0)
        elif opt in ('-x', '--execute'):
            setting.update(command = AdminCmdDef.EXECUTABLE.name)
        elif opt in ('-s', '--shutdown'):
            setting.update(command = AdminCmdDef.SHUTDOWN.name)
        elif opt in ('-r', '--restart'):
            setting.update(command = AdminCmdDef.RESTART.name)
        elif opt in ('--redirect', ):
            setting.update(command = AdminCmdDef.REDIRECT.name)
        elif opt in ('-c', '--console'):
            setting.update(console = val)
        elif opt in ('-d', '--daemonize'):
            setting.update(daemonize = True)
        elif opt in ('--without', ):
            setting['features'] = [ f for f in setting.get('features') if f.lower() != val.lower() ]
 
    return [setting, *args]

def do_client_request():
    print('Do client request')
    try:
        with socket.socket(socket.AF_UNIX) as sock:
            for _ in range(5):
                try:
                    sock.connect(SOCK_DEF)
                    sock.send(MainCmdDef.ADMIN.make_command(*sys.argv[1:]).encode('utf-8'))
                except (ConnectionError, FileNotFoundError):
                    time.sleep(1)
                else:
                    break
    except BaseException as e:
        print(e, type(e))

def main():
    pidfd = os.open(PID_FILE_DEF, os.O_CREAT | os.O_WRONLY )

    try:
        #It will unlock file after closing fd. No need to set LOCK_UN.
        fcntl.flock(pidfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Run as client")
        do_client_request()
        sys.exit(0)

    setting, *app_programs = parse_command_arguments(*sys.argv[1:])

    if setting.get('daemonize'):
        print('Run as daemon')
        if 0 < os.fork():
            # Parent only
            sys.exit(0)

        try:
            #os.chdir('/')
            # File permission value is equal to the difference between the values of chmod and umask.
            # For example, the value of chmod is 777, the value of umask is 022, and the file permission final value is 755
            # The child process will inherit all permissions from the parent process
            os.umask(0o0) 
            # Change SID to current PID. Detach process from the terminal.
            os.setsid()
        except BaseException as e:
            print(e, type(e))
            os.close(pidfd)
            sys.exit(0)

        if 0 < os.fork():
            # Parent only
            sys.exit(0)

        try:
            for fd in sys.stdin, sys.stdout, sys.stderr:
                fd.flush()
                fd.close()

            f0 = open(f'/dev/null', 'w+')
            os.dup2(f0.fileno(), sys.stdout.fileno())

            f1 = open(f'{{RUN_DIR_DEF}}/error.log', 'w+')
            os.dup2(f1.fileno(), sys.stderr.fileno())

            f2 = open('/dev/null', 'r')
            os.dup2(f2.fileno(), sys.stdin.fileno())

            # signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        except BaseException as e:
            print(e, type(e))
            os.close(pidfd)
            sys.exit(0)
    try:
        print("Sent parameters to unix socket and consume after the service started")
        threading.Thread(target = do_client_request).start()

        pidfo = os.fdopen(pidfd, 'w')
        pidfo.write("%d" % (os.getpid()))
        pidfo.flush()
        #pidfo.close()

        admin = AppAdminister(*app_programs, **setting)
        asyncio.run(admin.serve())
    finally:
        #Unlock file
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
'''