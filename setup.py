import sys
from cx_Freeze import Executable, setup

base = None
if sys.platform == "win32":
    base = "gui"

build_exe_options = {
    "build_exe": "dist",
    "includes": [
        "tkinter",
        "tkinter.messagebox",
        "tkinter.filedialog",
        "tkinter.scrolledtext",
        "tkinter.ttk",
    ],
    "include_files": [("res", "res")],
    "include_msvcr": True,
}

setup(
    name="aoe2de_patcher",
    version="2.12",
    description="AoE2DE patcher",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "src/aoe2de_patcher.py",
            base=base,
            target_name="aoe2de_patcher.exe",
        )
    ],
)
