import sys
import os
import shutil
import pefile
from pathlib import Path

from tkinter import Text


def is_dotnet_available() -> bool:
    """Checks if dotnet is available.

    Returns:
        bool: True if dotnet is available
    """
    return not (shutil.which("dotnet") is None)


def is_windows_platform() -> bool:
    return sys.platform == "win32"


def get_exe_name() -> str:
    return "AoE2DE_s.exe"


def get_binary_version(path: Path) -> tuple[int, int, int, int]:
    """Retrieve the version number of a binary file.

    Args:
        path (Path): The path to the file

    Returns:
        tuple: Windows version number
    """
    # Untested under linux, but I would assume it works..
    # TODO: Test
    with pefile.PE(path, fast_load=True) as pe:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])

        if not hasattr(pe, "VS_FIXEDFILEINFO") or not pe.VS_FIXEDFILEINFO:
            raise ValueError("Could not find VS_FIXEDFILEINFO in binary")

        file_info = pe.VS_FIXEDFILEINFO[0]

        version_number = (
            file_info.FileVersionMS >> 16,
            file_info.FileVersionMS & 0xFFFF,
            file_info.FileVersionLS >> 16,
            file_info.FileVersionLS & 0xFFFF
        )

        return version_number


def get_game_version(game_dir: Path) -> int:
    """Retrieve the game version from the executable file.

    Returns:
        int: The detected game version
    """
    metadata = get_binary_version(game_dir / get_exe_name())

    return (metadata[1] - 101) * 65536 + metadata[2]


def log(text_widget: Text, text: str) -> None:
    """Logs a given string to the text widget.

    Args:
        text_widget (Text): The text widget
        text (str): The text
    """
    text_widget.configure(state="normal")
    text_widget.insert("end", text)
    text_widget.configure(state="disabled")
    text_widget.see("end")


def delete_registry_value(registry_path: str, value_name: str) -> None:
    import winreg

    roots = {
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKEY_USERS": winreg.HKEY_USERS,
    }

    root_name, sub_key = registry_path.split("\\", 1)

    try:
        root = roots[root_name]
    except KeyError:
        raise ValueError(
            f"Unsupported registry root: {root_name}"
        )

    try:
        with winreg.OpenKey(
            root,
            sub_key,
            access=winreg.KEY_SET_VALUE | winreg.KEY_WOW64_32KEY,
        ) as key:
            winreg.DeleteValue(key, value_name)

    except FileNotFoundError:
        # Already in the desired state.
        pass


def clear() -> None:
    """Clear the screen of the console.
    """
    _ = os.system('cls')
