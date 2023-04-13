# -*- coding:utf-8 -*-
#!/usr/bin/env python

APP_START_DAEMON_COMMAND_CONTENT_DEF = '''#!/bin/bash
echo "Start $APP_NAME_DEF"
$admin_program_file -x -d
'''

APP_STOP_DAEMON_COMMAND_CONTENT_DEF = '''#!/bin/bash
echo "Stop $APP_NAME_DEF"
$admin_program_file -s
sleep 1
cat $run_dir/*.pid | xargs kill -9
rm -rf $run_dir/*
'''

APP_ENABLE_DAEMON_COMMAND_CONTENT_DEF = '''#!/bin/bash

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
'''

APP_DISABLE_DAEMON_COMMAND_CONTENT_DEF = '''#!/bin/bash

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
    find /usr/lib/systemd/ /lib/systemd/ /etc/systemd/ -name "\\$srv" -exec rm -f {{}} \\;
done

systemctl daemon-reload
systemctl reset-failed 
'''