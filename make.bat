@echo off
pyinstaller --onefile --name "aoe2patch_reverter" src/main.py --add-data "res;res" >nul 2>&1
@RD /S /Q "src/__pycache__"
@RD /S /Q "build" >nul 2>&1
if exist "build" rd /s /q "build"
DEL "aoe2patch_reverter.spec"

echo Build complete