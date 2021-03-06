#!/bin/bash

CURR_SCRIPT_DIR_DEF="$(readlink -f $0 | xargs dirname)"

pushd $CURR_SCRIPT_DIR_DEF

if [ "$1" == "-i" ]||[ ! -e venv/bin/python ]
then
    python3 -m venv --clear $CURR_SCRIPT_DIR_DEF/venv
    venv/bin/python -m pip install -r req/requirements.txt
    venv/bin/python -m pip install -e `realpath ../..`
fi

if [ -e venv ]
then
    venv/bin/python setup.py bdist_wheel bdist_app --rpm cleanup
fi

popd