$ErrorActionPreference = 'Stop'
$protoboostPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $protoboostPython)) {
    throw 'Set up .venv first using the commands in README.md.'
}
& $protoboostPython (Join-Path $PSScriptRoot 'protoboost.py')
exit $LASTEXITCODE
