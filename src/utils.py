import sys
import os
import pathlib
import shutil
import win32api

from tkinter import Text

def get_version_number (path: pathlib.Path):
  """Retrieve the version number of a binary file.

  Args:
      path (pathlib.Path): The path to the file

  Returns:
      list: Windows version number
  """
  info = win32api.GetFileVersionInfo(str(path), "\\")
  ms = info['FileVersionMS']
  ls = info['FileVersionLS']
  return win32api.HIWORD (ms), win32api.LOWORD (ms), win32api.HIWORD (ls), win32api.LOWORD (ls)

def log(text_widget: Text, text: str):
  """Logs a given string to the text widget.

  Args:
      text_widget (Text): The text widget
      text (str): The text
  """
  text_widget.configure(state="normal")
  text_widget.insert("end", text)
  text_widget.configure(state="disabled")
  text_widget.see("end")

def copy_file_or_dir(source_dir: pathlib.Path, target_dir: pathlib.Path, file: str):
  """Copies a file or a directory recursively into the target directory.

  Args:
      source_dir (pathlib.Path): The source directory
      target_dir (pathlib.Path): The target directory
      file (str): The file or directory name
  """
  if (source_dir / file).is_dir():
    shutil.copytree((source_dir / file).absolute(), (target_dir / file).absolute())
  else:
    shutil.copy((source_dir / file).absolute(), (target_dir / file).absolute())

def remove_file_or_dir(path: pathlib.Path):
  """Removes a file or directory recursively. Does not throw an error if file does not exist.

  Args:
      path (pathlib.Path): The path to be removed
  """
  if path.is_dir():
    shutil.rmtree(path.absolute(), ignore_errors=True)
  else:
    path.unlink(missing_ok=True)

def backup_files(original_dir: pathlib.Path, override_dir: pathlib.Path, backup_dir: pathlib.Path, debug_info: bool):
  """Recursively performs backup of original_dir to backup_dir assuming all files/folder from override_dir will be patched.

  Args:
      original_dir (pathlib.Path): The original directory
      override_dir (pathlib.Path): The directory containing files / directories that will be overridden
      backup_dir (pathlib.Path): The directory where the backup will be placed
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

def remove_patched_files(original_dir: pathlib.Path, override_dir: pathlib.Path, debug_info: bool):
  """Recursively removes all patched files assuming original_dir has been patched with all files from override_dir.

  Args:
      original_dir (pathlib.Path): The original directory
      override_dir (pathlib.Path): The directory containing the files that have been overridden
      debug_info (bool): Flag for printing debug info

  Raises:
      BaseException: If there was an error removing files
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
  except BaseException as e:
    raise e

def check_dotnet():
  """Checks if dotnet is available.

  Returns:
      bool: True if dotnext is available
  """
  return not (shutil.which("dotnet") is None)

def base_path():
  """Construct the base path to the exe / project.

  Returns:
      pathlib.Path: The base path of the exectuable or project
  """ 
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    return pathlib.Path(pathlib.sys.executable).parent
  else:
    return pathlib.Path()

def resource_path(relative_path: str):
  """Construct the resource patch for a resource.

  Args:
      relative_path (str): The path relative to the resource path

  Returns:
      pathlib.Path: The path to the given resource
  """
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = pathlib.Path(pathlib.sys._MEIPASS)
  else:
    base_path = pathlib.Path()

  return base_path / "res" / relative_path

def clear():   
  """Clear the screen of the console.
  """
  _ = os.system('cls')