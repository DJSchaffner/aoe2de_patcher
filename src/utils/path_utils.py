import sys
from pathlib import Path


def get_base_path() -> Path:
    """Construct the base path to the exe / project.

    Returns:
        Path: The base path of the executable or project
    """
    # Check for pyinstaller
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(getattr(sys, '_MEIPASS'))

    # Check for cx_Freeze
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        # On Windows, the executable is in the root directory
        return Path(sys.executable).parent

    if getattr(sys, 'frozen', False):
        # On Unix-like systems, check for common cx_Freeze structures
        base = Path(sys.executable).parent
        if (base / 'lib').exists():
            return base
        return base

    # Check for nuitka
    if "__compiled__" in globals() or hasattr(sys, 'nuitka_version_info'):
        return Path(sys.executable).parent

    # Running as script (expects to be inside root/src/utils)
    return Path(__file__).parent.parent.parent


def get_tools_path(relative_path: str) -> Path:
    """Construct the path for a tool.

    Args:
        relative_path (str): The path relative to the tools path

    Returns:
        Path: The path to the given tool
    """
    return get_base_path() / "tools" / relative_path
