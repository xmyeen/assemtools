param (
    [Parameter()]
    [switch]$i = $false
)

$CurrentScriptRoot = $PSScriptRoot
$ProjectRoot = Resolve-Path -Path "${CurrentScriptRoot}\..\..\"
$EnvRoot = "${CurrentScriptRoot}\venv"
$EnvPy = "${EnvRoot}\Scripts\python.exe"

Push-Location $CurrentScriptRoot

if ( Test-Path -Path "${CurrentScriptRoot}\dist"  ) {
    Remove-Item -Force -Recurse -Path "${CurrentScriptRoot}\dist\*"
}

if ( $i -or ( Test-Path -Path $EnvPy ) ) {
    python -m venv --clear $EnvRoot
    & "$EnvPy" -m pip install -r req/requirements.txt
    & "$EnvPy" -m pip install -e $ProjectRoot
}

if ( Test-Path -Path $EnvPy ) {
    & "$EnvPy" setup.py bdist_wheel bdist_app cleanup
}

Pop-Location