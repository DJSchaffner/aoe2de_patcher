import os
import shutil
from pathlib import Path


def copy_file_or_dir(source_dir: Path, target_dir: Path, file: str) -> None:
    """Copies a file or a directory recursively into the target directory.

    Args:
        source_dir (Path): The source directory
        target_dir (Path): The target directory
        file (str): The file or directory name
    """
    if (source_dir / file).is_dir():
        shutil.copytree((source_dir / file).absolute(), (target_dir / file).absolute())
    else:
        shutil.copy((source_dir / file).absolute(), (target_dir / file).absolute())


def remove_file_or_dir(path: Path) -> None:
    """Removes a file or directory recursively. Does not throw an error if file does not exist.

    Args:
        path (Path): The path to be removed
    """
    if path.is_dir():
        shutil.rmtree(path.absolute(), ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def find_files(path: Path, pattern: str = "*") -> list[Path]:
    """Finds all files matching the given pattern in a directory.

    Args:
        path (Path): The directory to scan
        pattern (str): The pattern to match

    Returns:
        list[str]: A list of matching files
    """
    return [x for x in path.glob(pattern) if x.is_file()]


def backup_files(original_dir: Path, override_dir: Path, backup_dir: Path, debug_info: bool) -> None:
    """Recursively performs backup of original_dir to backup_dir assuming all files/folder from override_dir will be patched.

    Args:
        original_dir (Path): The original directory
        override_dir (Path): The directory containing files / directories that will be overridden
        backup_dir (Path): The directory where the backup will be placed
        debug_info (bool): Flag for printing debug info
    """
    changed_file_list = list(set(os.listdir(original_dir.absolute())).intersection(set(os.listdir(override_dir.absolute()))))

    for file in changed_file_list:
        # Its a folder, backup its contents
        if (original_dir / file).is_dir():
            (backup_dir / file).mkdir()
            backup_files(original_dir / file, override_dir / file, backup_dir / file, debug_info)
        # Its a file, copy it
        else:
            if debug_info:
                print(f"Copy {(original_dir / file).absolute()}")

            copy_file_or_dir(original_dir, backup_dir, file)


def remove_patched_files(original_dir: Path, override_dir: Path, debug_info: bool) -> None:
    """Recursively removes all patched files assuming original_dir has been patched with all files from override_dir.

    Args:
        original_dir (Path): The original directory
        override_dir (Path): The directory containing the files that have been overridden
        debug_info (bool): Flag for printing debug info

    Raises:
            Exception: If there was an error removing files
    """
    changed_file_list = os.listdir(override_dir.absolute())

    # Remove all overridden files
    try:
        for file in changed_file_list:
            # Its a folder, remove its contents
            if (original_dir / file).is_dir():
                remove_patched_files(original_dir / file, override_dir / file, debug_info)

                # Remove directory if its now empty
                if len(os.listdir((original_dir / file).absolute())) == 0:
                    if debug_info:
                        print(f"Remove {(original_dir / file).absolute()}")

                    remove_file_or_dir(original_dir / file)
            # Its a file, remove it
            else:
                if debug_info:
                    print(f"Remove {(original_dir / file).absolute()}")

                remove_file_or_dir(original_dir / file)
    except Exception as e:
        raise e
