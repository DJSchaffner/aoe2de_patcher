# Utils
import sys
import os
import pathlib
import shutil
import locale
import re
import time
import win32api

from tkinter import Text

def get_version_number (path: pathlib.Path):
  """Retrieve the version number of a binary file."""  
  info = win32api.GetFileVersionInfo(str(path), "\\")
  ms = info['FileVersionMS']
  ls = info['FileVersionLS']
  return win32api.HIWORD (ms), win32api.LOWORD (ms), win32api.HIWORD (ls), win32api.LOWORD (ls)

def log(text_widget: Text, text: str):
  """Logs a given string to the text widget."""
  text_widget.configure(state="normal")
  text_widget.insert("end", text)
  text_widget.configure(state="disabled")
  text_widget.see("end")

def copy_file_or_dir(source_dir: pathlib.Path, target_dir: pathlib.Path, file: str):
  """Copies a file or a directory recursively into the target directory."""
  if (source_dir / file).is_dir():
    shutil.copytree((source_dir / file).absolute(), (target_dir / file).absolute())
  else:
    shutil.copy((source_dir / file).absolute(), (target_dir / file).absolute())

def remove_file_or_dir(dir, file):
  """Removes a file or directory recursively. Does not throw an error if file does not exist."""  
  if (dir / file).is_dir():
    shutil.rmtree((dir / file).absolute(), ignore_errors=True)
  else:
    (dir / file).unlink(missing_ok=True)

def backup_files(original_dir: pathlib.Path, override_dir: pathlib.Path, backup_dir: pathlib.Path):
  """Recursively performs backup of original_dir to backup_dir assuming all files/folder from override_dir will be patched."""
  changed_file_list = list(set(os.listdir(original_dir.absolute())).intersection(set(os.listdir(override_dir.absolute()))))

  for file in changed_file_list:
    if (original_dir / file).is_dir():
      (backup_dir / file).mkdir()
      backup_files(original_dir / file, override_dir / file, backup_dir / file)
    else:
      copy_file_or_dir(original_dir, backup_dir, file)

def remove_patched_files(original_dir: pathlib.Path, override_dir: pathlib.Path):
  """Recursively removes all patched files assuming original_dir has been patched with all files from override_dir."""
  changed_file_list = os.listdir(override_dir.absolute())

  # Remove all overridden files
  for file in changed_file_list:
    if (original_dir / file).is_dir():
      remove_patched_files(original_dir / file, override_dir / file)

      # Remove directory if its now empty
      if len(os.listdir((original_dir / file).absolute())) == 0:
        try:
          remove_file_or_dir(original_dir, file)
        except BaseException as e:
          raise e
    else:
      try:
        remove_file_or_dir(original_dir, file)
      except BaseException as e:
        raise e

def check_dotnet():
  """Checks if dotnet is available."""
  return not (shutil.which("dotnet") is None)

def base_path():
  """Construct the base path to the exe / project."""
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    return pathlib.Path(pathlib.sys.executable).parent
  else:
    return pathlib.Path()

def resource_path(relative_path):
  """Construct the resource patch for a resource."""
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = pathlib.Path(pathlib.sys._MEIPASS)
  else:
    base_path = pathlib.Path()

  return base_path / "res" / relative_path

def clear():   
  """Clear the screen of the console."""  
  _ = os.system('cls')