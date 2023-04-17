import sys
import os
import pathlib
import shutil
import signal
import tempfile
import re
import time
from queue import Queue
from dataclasses import dataclass

import pexpect
import pexpect.popen_spawn
import tkinter
import tkinter.simpledialog

from webhook import Webhook
import utils

@dataclass
class Manifest():
  depot: int
  id: int
  date: int
  num_files: int
  num_chunks: int
  size_disk: int
  size_compressed: int
  files: list

class Logic:
  app_id = 813780

  def __init__(self):
    self.webhook = Webhook()
    # The earliest patch that works was released after directx update
    # @TODO Try to figure out a way to patch to earlier patches than this
    #self.directx_update_date = time.struct_time((2020, 2, 17, 0, 0, 0, 0, 48, 0))
    self.download_dir = utils.base_path() / "download"
    self.manifest_dir = utils.base_path() / "manifests"
    self.backup_dir = utils.base_path() / "backup"
    self.patch_list = self.webhook.query_patches()
    self.process_queue = Queue()

  def patch(self, username: str, password: str, target_version: int):
    """Start patching the game with the downloaded files.

    Args:
        username (str): The username
        password (str): The password
        target_version (int): The version to patch to
    """
    success = True

    # Check some stuff
    if not hasattr(self, "game_dir") or self.game_dir is None:
      print("Please select a game directory")
      return

    if username == "":
      print("Please enter a username")
      return

    if password == "":
      print("Please enter a password")
      return

    if self.installed_version == target_version:
      print("The selected version is already installed")
      return

    # Always true
    if success:
      print("Starting download phase")
      success = success and self._download_patch(username, password, target_version)

      if not success:
        print("Error during download!")

    if success:
      print("Starting backup")
      success = success and self._backup()

      if not success:
        print("Error during backup!")

    if success:
      print("Patching files")
      success = success and self._move_patch()

      if not success:
        print("Error during patch!")

    if success:
      print("DONE!")
    else:
      print("Could not patch!")

  def restore(self):
    """Restores the game directory using the backed up files and downloaded files.
    """
    # Check some stuff
    if not hasattr(self, "game_dir") or self.game_dir is None:
      print("Please select a game directory")
      return

    if not self.backup_dir.exists():
      print("Backup directory doesn't exist")
      return

    if len(os.listdir(self.backup_dir.absolute())) == 0:
      print("No backup stored")
      return

    # Remove added files from the path
    try:
      print("Removing patched files")
      utils.remove_patched_files(self.game_dir, self.download_dir, True)
      print("Finished removing patched files")

      # Copy backed up files to game path again
      try:
        print("Restoring backup...")
        shutil.copytree(self.backup_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok=True)
        print("Finished restoring backup")
        print("DONE!")
      except BaseException:
        print("Error restoring files!")
    except BaseException:
      print("Error removing files!")

  def set_game_dir(self, dir: pathlib.Path):
    """Tries to set the game directory, if succesful return True. Otherwise return False.

    Args:
        dir (pathlib.Path): The directory to be set

    Returns:
        bool: True if successful
    """
    aoe_binary = dir / "AoE2DE_s.exe"

    if aoe_binary.exists():
      self.game_dir = dir
      self.installed_version = self._get_game_version()

      print(f"Game directory set to: {dir.absolute()}")
      print(f"Installed version detected: {self.installed_version}")
      return True

    print("Invalid game directory")
    return False

  def get_patch_list(self):
    """Returns the patch list.

    Returns:
        list: The list of documented patches
    """
    return self.patch_list

  def cancel_downloads(self):
    """Performs cleanup for logic object.
    """
    # Terminate all child processes
    for process in self.process_queue.queue:
      process.kill(signal.SIGTERM)

  def _download_patch(self, username: str, password: str, target_version: int):  
    """Download the given patch using the steam account credentials.

    Args:
        username (str): The username
        password (str): The password
        patch (dict): The dict containing patch info
        language (Languages): The selected language

    Returns:
        bool: True if successful
    """
    # dotnet is required to proceed
    if not (utils.check_dotnet()):
      print("DOTNET Core required but not found!")
      return False
    
    update_list = []   
    tmp_files = []

    # Remove previous download folder if it exists
    # Create empty folders afterwards
    if self.download_dir.exists():
      try:
        shutil.rmtree(self.download_dir.absolute())
      except BaseException:
        print("Error removing previous download directory")
        return False
    self.download_dir.mkdir()

    # Remove previous manifests folder if it exists
    # Create empty folders afterwards
    if self.manifest_dir.exists():
      try:
        shutil.rmtree(self.manifest_dir.absolute())
      except BaseException:
        print("Error removing previous manifest directory")
        return False
    self.manifest_dir.mkdir()

    print("Generating list of changes")

    # Filter list of patches for current and target version
    filtered_patches = list(filter(lambda x: x["version"] == self.installed_version or x["version"] == target_version, self.patch_list))

    # One of the two patches is not in the list of patches. Most likeley the installed version, cannot patch
    if len(filtered_patches) != 2:
      print("The installed version currently doesn't support downgrading. Please be patient or notify me on GitHub!")
      return False

    # Store current and target patch
    current_patch = list(filter(lambda x: x["version"] == self.installed_version, self.patch_list))[0]
    target_patch = list(filter(lambda x: x["version"] == target_version, filtered_patches))[0]

    # Only support patching via filelists to an older version atm
    if self.installed_version < target_version:
      print("Patching forward is currently unavailable. Please use Steam to get to the latest version and then patch backwards")
      return False

    # Iterate depots of current and target patch together
    for current_depot, target_depot in zip(current_patch["depots"], target_patch["depots"]):
      # Check if depot id changes (VCRedist for example does change sometimes)
      # (Temporary?) solution just skip non-matching depot since old depots are no longer available and hope it still works
      if current_depot["depot_id"] == target_depot["depot_id"]:
        depot_id = current_depot["depot_id"]
        current_manifest_id = current_depot["manifest_id"]
        target_manifest_id = target_depot["manifest_id"]

        changes = self._get_filelist(username, password, depot_id, current_manifest_id, target_manifest_id)

        # Files have changed, store changes to temp file and add to update list
        if not changes is None:
          # Create temp file
          tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)

          # Store file name for deletion later on
          tmp_files.append(tmp.name)

          # Write content to file
          tmp.write("\n".join(changes))
          tmp.close()

          # Add update element to list
          update_list.append({ 'depot_id': depot_id, 'manifest_id': target_manifest_id, 'filelist': tmp.name })
      else:
        print(f"Depot ID not matching, discarding pair ({current_depot['depot_id']}, {target_depot['depot_id']})")
   
    print("Downloading files")
    
    # Loop all necessary updates
    for element in update_list:
      # Stop if a download didn't succeed
      if not self._download_depot(username, password, element['depot_id'], element['manifest_id'], element['filelist']):
        return False

    # Remove created temp files
    for tmp in tmp_files:
      os.unlink(tmp)

    return True

  def _move_patch(self):
    """Move downloaded patch files to game directory.

    Returns:
        bool: True if successful
    """
    try:
      shutil.copytree(self.download_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok=True)

      return True
    except BaseException:
      pass

    return False

  def _backup(self):
    """Backup game folder and in current directory.

    Returns:
        bool: True if successful
    """
    try:
      # Remove previous backup folder if it exists
      # Create empty folders afterwards
      if self.backup_dir.exists():
        try:
          shutil.rmtree(self.backup_dir.absolute())
        except BaseException:
          print("Error removing previous backup directory")
          return False
      self.backup_dir.mkdir()

      utils.backup_files(self.game_dir, self.download_dir, self.backup_dir, True)

      return True
    except BaseException:
      pass

    return False

  def _depot_downloader(self, options: list):
    """Execute the DepotDownloader with the given options as arguments. Return True if successfull.

    Args:
        options (list): A list of options that will be passed to DepotDownloader directly

    Raises:
        ConnectionError: If there was an error during authentication

    Returns:
        bool: True if successful
    """
    success = False
    depot_downloader_path = f"\"{str(utils.resource_path('DepotDownloader/DepotDownloader.dll').absolute())}\""

    args = ["dotnet", depot_downloader_path] + options
    
    # Spawn process and store in queue
    p = pexpect.popen_spawn.PopenSpawn(" ".join(args), encoding="utf-8")
    self.process_queue.put(p)
    p.logfile_read = sys.stdout

    try:
      responses = [
        "result: OK",
        "Please enter .*: ",
        pexpect.EOF
      ]

      # Default timeout in seconds
      timeout = 15
      response = p.expect(responses, timeout=timeout)

      # Success
      if response == 0:
        success = True

      # Code required
      elif response == 1:        
        # Open popup for 2FA Code
        # Create temporary parent window to prevent error with visibility
        temp = tkinter.Tk()
        temp.withdraw()
        code = tkinter.simpledialog.askstring(title="Code", prompt="Please enter your 2FA login code", parent=temp)
        temp.destroy()

        # Cancel was clicked
        if code is None:
          raise ConnectionError("Invalid authentication code")
        # Code was entered
        else:
          # Send 2fa code to child process and check the result
          p.sendline(code)

          # Invalid code
          if p.expect(responses, timeout=timeout) == 1:
            raise ConnectionError("Invalid authentication code")
          # Success
          else:
            success = True

      # Error
      elif response == 2:
        raise ConnectionError("Error logging into account")

      # Wait for program to finish
      p.expect(pexpect.EOF, timeout=None)
    except pexpect.exceptions.TIMEOUT as e:
      print("Error waiting for DepotDownloader to start")
    except ConnectionError as e:
      print(e)
    finally:
      # Remove process from queue after working with it
      self.process_queue.get()

    return success

  def _download_manifest(self, username: str, password: str, depot_id: int, manifest_id: int):
    """Download a specific manifest from the given depot using the given credentials.

    Args:
        username (str): The username
        password (str): The password
        depot_id (int): The selected depot
        manifest_id (int): The manifest id for the depot

    Raises:
        ConnectionError: If there was an error during authentication

    Returns:
        bool: True if successful
    """
    args = ["-app", str(self.app_id), 
            "-depot", str(depot_id), 
            "-manifest", str(manifest_id), 
            "-username", username, 
            "-password", password, 
            "-remember-password",
            "-dir", str(self.manifest_dir),
            "-manifest-only"]

    return self._depot_downloader(args)

  def _download_depot(self, username: str, password: str, depot_id: int, manifest_id: int, filelist: str):
    """Download a specific depot using the manifest id from steam using the given credentials.

    Args:
        username (str): The username
        password (str): The password
        depot_id (int): The selected depot
        manifest_id (int): The manifest id for the depot
        filelist (str): The name of the file used as filelist

    Raises:
        ConnectionError: If there was an error during authentication

    Returns:
        bool: True if successful
    """
    args = ["-app", str(self.app_id), 
            "-depot", str(depot_id), 
            "-manifest", str(manifest_id), 
            "-username", username, 
            "-password", password, 
            "-remember-password",
            "-dir", str(self.download_dir),
            "-filelist", filelist]

    return self._depot_downloader(args)

  def _get_filelist(self, username: str, password: str, depot_id: int, current_manifest_id: int, target_manifest_id: int):
    """Get a list of all files that have been removed or modified between the current and target version.

    Args:
        username (str): The username
        password (str): The password
        depot_id (int): The selected depot
        current_manifest_id (int): The current manifest id for the depot
        target_manifest_id (id): The target manifest id for the depot

    Returns:
        list: A list of changed filenames
    """
    # Only need to check for changes if manifest changed
    if current_manifest_id == target_manifest_id:
      return None

    removed = []
    modified = []

    # Download manifests
    self._download_manifest(username, password, depot_id, current_manifest_id)
    self._download_manifest(username, password, depot_id, target_manifest_id)

    # Read manifest files
    current_manifest = self._read_manifest(self.manifest_dir / f"manifest_{depot_id}_{current_manifest_id}.txt")
    target_manifest = self._read_manifest(self.manifest_dir / f"manifest_{depot_id}_{target_manifest_id}.txt")

    # Initialize file sets
    current_set = set(current_manifest.files)
    target_set = set(target_manifest.files)

    # Find all removed files (Result contains removed files and files with different hash)
    diff_removed = list(target_set.difference(current_set))
    diff_removed_names = set([x[0] for x in diff_removed])

    # Find all added files (Result contains added files and files with different hash)
    diff_added = list(current_set.difference(target_set))
    diff_added_names = set([x[0] for x in diff_added])
    
    # Find all removed files (Remove files with same name but different hash)
    removed = set.difference(diff_removed_names, diff_added_names)

    # Find all modified files (Retain files with same name but different hash)
    modified = set.intersection(diff_removed_names, diff_added_names)

    changes = []

    changes += removed
    changes += modified

    return changes

  def _get_filelist_current(self, username: str, password: str, depot_id: int, manifest_id: int):
    """Get a list of all files current files of a depot.

    Args:
        username (str): The username
        password (str): The password
        depot_id (int): The selected depot
        manifest_id (int): The current manifest id for the depot

    Returns:
        list: A list of current filesnames for the depot
    """
    # Download manifests
    self._download_manifest(username, password, depot_id, manifest_id)

    # Read manifest files
    current_manifest = self._read_manifest(self.manifest_dir / f"manifest_{depot_id}_{manifest_id}.txt")

    return current_manifest.files

  def _read_manifest(self, file: pathlib.Path):
    """Parse a given manifest file and return a manifest object

    Args:
        file (pathlib.Path): Path to the manifest file

    Returns:
        Manifest: The parsed manifest object
    """
    result = None

    with open(file, "r") as f:
      depot = 0
      id = 0
      date = 0
      num_files = 0
      num_chunks = 0
      size_disk = 0
      size_compressed = 0
      files = []

      line = f.readline() # First line contains depot id
      depot = re.match(r".* (\d+)", line).groups()[0]

      # Second lines is empty
      # Third contains manifest id and date
      line = f.readline()
      line = f.readline()
      groups = re.match(r".* : (\d+) \/ (.+)", line).groups()
      id = groups[0]
      date = groups[1] # (Temporary) workaround since date isn't used anyways. 
      # Date format seems to be localized... @TODO find a way to universally parse datestring
      #date = time.mktime(time.strptime(groups[1], "%d.%m.%Y %H:%M:%S"))

      # Fourth line contains number of files
      line = f.readline()
      groups = re.match(r".* : (\d+)", line).groups()
      num_files = groups[0]

      # Fifth line contains number of chunks
      line = f.readline()
      groups = re.match(r".* : (\d+)", line).groups()
      num_chunks = groups[0]

      # Sixth line contains size on disk
      line = f.readline()
      groups = re.match(r".* : (\d+)", line).groups()
      size_disk = groups[0]

      # Seventh line contains size compressed
      line = f.readline()
      groups = re.match(r".* : (\d+)", line).groups()
      size_compressed = groups[0]

      # Eighth line is empty
      # Nineth line contains headers
      # Tenth line until EOF contains one file per line
      line = f.readline()
      line = f.readline()
      while line := f.readline():
        groups = re.match(r"\s+\d+\s+\d+\s+(.{40})\s+\d+\s+(.+)", line)
        files.append((groups[2], groups[1]))

      result = Manifest(depot, id, date, num_files, num_chunks, size_disk, size_compressed, files)

    return result

  def _get_game_version(self):
    """Retrieve the game version from the executable file. Requires game directory to be set.

    Returns:
        int: The detected game version
    """
    metadata = utils.get_version_number(self.game_dir / "AoE2DE_s.exe")

    return (metadata[1] - 101) * 65536 + metadata[2]