# Utils
import sys
import pathlib

def base_path():
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    return pathlib.Path(pathlib.sys._MEIPASS)
  else:
    return pathlib.Path()

def resource_path(relative_path):
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = pathlib.Path(pathlib.sys._MEIPASS)
  else:
    base_path = pathlib.Path()

  return base_path / "res" / relative_path

def clear():   
  _ = os.system('cls')