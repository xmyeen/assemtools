#!/bin/sh

function check_python() {
    pycmd="$1"

cat << EOF | $pycmd -
import sys, zipfile
from pip._internal.utils.packaging import check_requires_python, get_requires_python,get_metadata
from pip._internal.utils.wheel import pkg_resources_distribution_for_wheel

local_file_path = "tests/x/dist/x-1.0.0-py3-none-any.whl"

with zipfile.ZipFile(local_file_path, allowZip64 = True) as z:
    dist = pkg_resources_distribution_for_wheel(z, 'x', local_file_path)
    pkg_info = get_metadata(dist)
    python_require =pkg_info.get('Requires-Python')
    sys.exit(0 if not python_require or check_requires_python(python_require, sys.version_info[:3]) else 1)
EOF

}

$(check_python `which python3`) && echo "yes"