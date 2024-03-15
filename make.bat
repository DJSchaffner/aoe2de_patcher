call .venv\Scripts\activate
call python -m nuitka --enable-plugin=tk-inter --include-data-dir=res=res --standalone --follow-imports --remove-output --windows-disable-console src/aoe2de_patcher.py
call .venv\Scripts\deactivate
xcopy res aoe2de_patcher.dist\res /s /y
echo Build complete