@echo off
SETLOCAL

if "%~1"=="" (
    set version=2026
) else (
    set version=%~1
)

"C:/Program Files/Autodesk/Maya%version%/bin/mayapy.exe" -m src --cache "generated-stubs/%version%/cmds.pyi"

ENDLOCAL