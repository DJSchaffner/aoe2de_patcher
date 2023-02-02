import sys
import win32api

def get_version_number_win32 (path: str):
  """Retrieve the version number of a binary file.

  Args:
      path (str): The path to the file

  Returns:
      tuple: Windows version number
  """
  info = win32api.GetFileVersionInfo(path, "\\")
  ms = info['FileVersionMS']
  ls = info['FileVersionLS']
  return win32api.HIWORD (ms), win32api.LOWORD (ms), win32api.HIWORD (ls), win32api.LOWORD (ls)

if __name__ == '__main__':
    path = sys.argv[1]
    version = get_version_number_win32(path)
    sys.stdout.write(" ".join([str(x) for x in version])+"\n")
