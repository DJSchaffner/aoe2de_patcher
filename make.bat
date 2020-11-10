@echo off
pyinstaller --noconfirm --name "aoe2de_patcher" src/main.py --add-data "res;res" --noconsole >nul 2>&1
@RD /S /Q "src/__pycache__"
@RD /S /Q "build" >nul 2>&1
if exist "build" rd /s /q "build"
DEL "aoe2de_patcher.spec"

echo Build complete