# Utils
import sys
import os
import pathlib
import shutil
import locale
import re
from datetime import datetime

from tkinter import Text

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
    shutil.rmtree((dir / file).absolute())
  else:
    (dir / file).unlink(missing_ok=True)

def extract_date(date_string: str):
  """Extract a date in the format of 'd(d) Monthname yyyy'.

  Returns a datetime object
  """

  date_stripped = re.search(r"\d+ \w* \d+", date_string).group(0)
  
  locale.setlocale(locale.LC_TIME, "en_US")
  date = datetime.strptime(date_stripped, "%d %B %Y") 
  locale.setlocale(locale.LC_TIME, "de_DE")

  return date

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