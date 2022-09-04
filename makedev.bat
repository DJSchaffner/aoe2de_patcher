call .venv\Scripts\activate
call python -m nuitka --enable-plugin=tk-inter --include-data-dir=res=res --standalone --follow-imports --remove-output src/aoe2de_patcher.py
call .venv\Scripts\deactivate
echo Build complete