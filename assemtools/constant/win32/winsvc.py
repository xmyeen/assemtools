# -*- coding:utf-8 -*-
#!/usr/bin/env python

WIN32_APP_AGENT_SERVICE_DEF = '''# -*- coding:utf-8 -*-

import socket, logging, inspect, os, sys, time, warnings, subprocess, time, signal
import win32serviceutil, win32service, win32event, winerror, win32api, servicemanager

SHUTDOWN_MAX_TIMEOUT_SECOND_DEF = 5
PROGRAM_NAME_DEF = "{APP_PROGRAM_NAME}"

class ServerSrv(win32serviceutil.ServiceFramework):
    _svc_name_ = "{APP_WINSVC_AGENT_NAME}"
    _svc_display_name_ = "{APP_WINSVC_AGENT_NAME}"
    _svc_description_ = "{APP_DESCRIPTION}"
    _exe_name_ = "{APP_WINSVC_EXECUTABLE}"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.__shutdown_event = win32event.CreateEvent(None,  0, 0, None)
        self.__process_info = {{ name : None for name in PROGRAM_NAME_DEF.split(" ") }}
        self.__is_running = False
        # self.__logger = self.__get_logger()
        socket.setdefaulttimeout(60)

    @classmethod
    def parse_command_line(cls):
        win32serviceutil.HandleCommandLine(cls)

    # def __get_logger(self):
    #     log_root = os.path.join("{APP_ROOT}", "log", "winsvc")
    #     if not os.path.exists(log_root): os.makedirs(log_root)
    #     # this_file = inspect.getfile(inspect.currentframe())
    #     # dirpath = os.path.abspath(os.path.dirname(this_file))

    #     logger = logging.getLogger("{APP_WINSVC_AGENT_NAME}")
    #     handler = logging.FileHandler(os.path.join(log_root, "{APP_WINSVC_AGENT_NAME}.log"))
    #     formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    #     handler.setFormatter(formatter)
    #     logger.addHandler(handler)
    #     logger.setLevel(logging.INFO)
    #     return logger

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def SvcStop(self):
        self.log('[INFO] Stop now.')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.shutdown()

        sleeping_duration_sec, curr_duration_sec = 0.1, 0
        while curr_duration_sec < SHUTDOWN_MAX_TIMEOUT_SECOND_DEF:
            time.sleep(sleeping_duration_sec)
            curr_duration_sec += sleeping_duration_sec
            if not self.__is_running: break
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        self.log('[INFO] Stopped.')

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log('[INFO] Enter main')
            self.main()
            self.log('[INFO] Exit main')
            win32event.WaitForSingleObject(self.__shutdown_event, win32event.INFINITE)
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        except Exception as e:
            self.log('[ERR] Exception :' + str(e))
            self.SvcStop()

    def shutdown(self):
        win32event.SetEvent(self.__shutdown_event)

    def __keepAliveAll(self):
        new_process_info = {{}}

        for name, process in self.__process_info.items():
            try:
                if process and process.poll() is None: continue

                program_executable = os.path.join("{APP_ROOT}", "Scripts", "%s.exe" %(name))
                p = subprocess.Popen(program_executable, cwd = "{APP_ROOT}")
                self.log("[INFO] Execute %s" % (program_executable))
                new_process_info.update({{ name : p }})
            except Exception as e:
                self.log('[ERR] Exception :' + str(e))

        self.__process_info.update(new_process_info)

    def __terminiateAll(self):
        for name, process in self.__process_info.items():
            try:
                if not process or (process is not None): continue
                self.log("[INFO] Terminiate %s" % (name))
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            except Exception as e:
                self.log('[ERR] Exception :' + str(e))

        sleeping_duration_sec, curr_duration_sec = 0.5, 0
        while curr_duration_sec < SHUTDOWN_MAX_TIMEOUT_SECOND_DEF:
            time.sleep(sleeping_duration_sec)
            curr_duration_sec += sleeping_duration_sec
            if all([process.poll() is not None for _, process in self.__process_info.items()]):
                break
        else:
            for name, process in self.__process_info.items():
                try:
                    self.log("[INFO] Kill %s" % (name))
                    os.kill(process.pid, signal.SIGTERM)
                except Exception as e:
                    self.log('[ERR] Exception :' + str(e))

    def main(self):
        self.__is_running = True
        while self.__is_running:
            self.__keepAliveAll()
            rc = win32event.WaitForSingleObject(self.__shutdown_event, 5)
            # Check to see if shutting down
            if rc == win32event.WAIT_OBJECT_0:
                self.__terminiateAll()
                break
        self.__is_running = False

def ctrlHandler(ctrlType):
    return True

def main():
    if 1 == len(sys.argv):
        try:
            evtsrc_dll = os.path.abspath(servicemanager.__file__)
            servicemanager.PrepareToHostSingle(ServerSrv)
            servicemanager.Initialize('ServerSrv', evtsrc_dll)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error as e:
            if e == winerror.ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
                win32serviceutil.usage()
            warnings.warn(e)
        except Exception as e:
            warnings.warn(e)
    else:
        # ServerSrv.parse_command_line()
        win32serviceutil.HandleCommandLine(ServerSrv)

if __name__ == '__main__':
    main()
'''