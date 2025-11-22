@echo off
SETLOCAL

if "%~1"=="" (
    set version=2026
) else (
    set version=%~1
)

echo Generating stubs for Maya %version%

echo Installing dependencies...
"C:/Program Files/Autodesk/Maya%version%/bin/mayapy.exe" -m pip install -r generator/requirements.txt --target=./env
SET PYTHONPATH=%CD%/generator;%CD%/env;%PYTHONPATH%

echo Generating stubs...
"C:/Program Files/Autodesk/Maya%version%/bin/mayapy.exe" -m src --cache "generated-stubs/%version%/cmds.pyi"

ENDLOCAL