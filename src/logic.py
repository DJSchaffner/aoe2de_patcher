import sys
import os
import pathlib
import shutil
import signal
import tempfile
import time
from enum import IntEnum
from queue import Queue
from collections import defaultdict

import pexpect
import pexpect.popen_spawn
import tkinter
import tkinter.simpledialog
from steam.client import SteamClient

from webhook import Webhook
import utils

class Languages(IntEnum):
  BR = 0,
  DE = 1,
  EN = 2,
  FR = 3,
  IT = 4,
  KO = 5,
  MX = 6,
  ZH = 7,
  ZHH = 8

class Logic:
  app_id = 813780

  ignored_depots = [
    228987,  # VC 2017 Redist
    228990,  # DirectX
    1039811, # Encrypted DLC (Unknown)
    1022220, # Enhanced Graphics (Very large)
    1022226, # Soundtrack Depot
    1039810  # Soundtrack Depot
  ]

  dlc_depots = [
    1389240  # Palermo
  ] 

  language_depots = [
    813785,  # BR
    813786,  # DE
    813787,  # EN
    813788,  # FR
    813789,  # IT
    1022221, # KO
    1022222, # MX
    1022223, # ZH
    1022224, # ZH-Hant
    1022225  # ES
  ]

  def __init__(self):
    self.webhook = Webhook()
    # The earliest patch that works was released after directx update
    # @TODO Try to figure out a way to patch to earlier patches than this
    #self.directx_update_date = time.struct_time((2020, 2, 17, 0, 0, 0, 0, 48, 0))
    self.download_dir = utils.base_path() / "download"
    self.backup_dir = utils.base_path() / "backup"
    self.patch_list = self.webhook.query_patches()
    self.depot_list = self._get_depot_list()
    self.process_queue = Queue()

  def patch(self, username: str, password: str, patch: dict, language: Languages):
    """Start patching the game with the downloaded files."""
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

    self.installed_version = utils.get_version_number(self.game_dir / "AoE2DE_s.exe")[2]

    if self.installed_version == patch['version']:
      print("The selected version is already installed")
      return

    # Always true
    if success:
      print("Starting download phase")
      success = success and self._download_patch(username, password, patch, language)

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
    """Restores the game directory using the backed up files and downloaded files."""
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
        print("Restoring backup")
        shutil.copytree(self.backup_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok=True)
        print("Finished restoring backup")
        print("DONE!")
      except BaseException:
        print("Error restoring files!")
    except BaseException:
      print("Error removing files!")

  def set_game_dir(self, dir: pathlib.Path):
    """Tries to set the game directory, if succesful return True. Otherwise return False"""
    aoe_binary = dir / "AoE2DE_s.exe"

    if aoe_binary.exists():
      self.game_dir = dir

      print(f"Game directory set to: {dir.absolute()}")
      print(f"Installed version detected: {utils.get_version_number(aoe_binary)[2]}")
      return True

    print("Invalid game directory")
    return False

  def get_patch_list(self):
    """Returns the patch list"""
    return self.patch_list

  def cancel_downloads(self):
    """Performs cleanup for logic object."""
    # Terminate all child processes
    for process in self.process_queue.queue:
      process.kill(signal.SIGTERM)

  def _download_patch(self, username: str, password: str, patch: dict, language: Languages):  
    """Download the given patch in a language using the steam account credentials."""
    # dotnet is required to proceed
    if not (utils.check_dotnet()):
      print("DOTNET Core required but not found!")
      return False
    
    relevant_depots = []
    update_list = []   
    tmp_files = []
    filelists_result = None 

    # Remove previous download folder if it exists
    # Create empty folders afterwards
    if self.download_dir.exists():
      try:
        shutil.rmtree(self.download_dir.absolute())
      except BaseException:
        print("Error removing previous download directory")
        return False
    self.download_dir.mkdir()

    print("Preparing download")

    # Generate list of relevant depots for patch
    for depot in self.depot_list:
      if  ( (not (depot in self.ignored_depots)) and 
            (not (depot in self.dlc_depots)) and 
            ((not (depot in self.language_depots)) or (self.language_depots[language] == depot)) ):
        relevant_depots.append(depot)

    # Only support patching via filelists to an older version atm
    if self.installed_version < patch['version']:
      print("Patching forward is currently unavailable. Please use Steam to get to the latest version and then patch backwards")
      return False

    # Get a list of all filelists down to wanted version
    filelists_result = self._get_filelists(patch['version'], relevant_depots)

    for entry in filelists_result: 
      # Create temp file
      tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)

      # Store file name for deletion later on
      tmp_files.append(tmp.name)

      # Write content to file
      tmp.write(entry['filelist'])
      tmp.close()

      # Add update element to list
      update_list.append({ 'depot': entry['depot'], 'manifest': entry['manifest'], 'filelist': tmp.name })
   
    print("Downloading files")

    # Loop all necessary updates
    for element in update_list:
      # Stop if a download didn't succeed
      if not self._download_depot(username, password, patch['version'], element['depot'], element['manifest'], element['filelist']):
        return False

    # Remove created temp files
    for tmp in tmp_files:
      os.unlink(tmp)

    return True

  def _move_patch(self):
    """Move downloaded patch files to game directory."""
    try:
      shutil.copytree(self.download_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok=True)

      return True
    except BaseException:
      pass

    return False

  def _backup(self):
    """Backup game folder and in current directory.
    
    Returns True if everything worked, otherwise False"""
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

  def _download_depot(self, username: str, password: str, version: int, depot_id: int, manifest_id: int, filelist: str):
    """Download a specific depot using the manifest id from steam using the given credentials."""
    success = False
    depot_downloader_path = str(utils.resource_path("DepotDownloader/DepotDownloader.dll").absolute())
    args = ["dotnet", f'"{depot_downloader_path}"', 
            "-app", str(self.app_id), 
            "-depot", str(depot_id), 
            "-manifest", str(manifest_id), 
            "-username", username, 
            "-password", password, 
            "-remember-password",
            "-dir download"]

    if not filelist is None:
      args.append(f"-filelist {filelist}")

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

  def _get_depot_list(self):
    """Get a list of depots for the app.

    Returns the list of depots
    """    
    result = []

    client = SteamClient()
    client.anonymous_login()

    info = client.get_product_info(apps=[self.app_id])

    for depot in list(info['apps'][self.app_id]['depots']):
      # Only store depots with numeric value
      if depot.isnumeric():
        result.append(int(depot))

    return result    

  def _get_filelists(self, selected_version, relevant_depots):
    """Get a list of all filelists between the current version and the selected one for all the relevant depots.
    If any patch in between does not have a filelist stored, None will be returned.

    Returns a list of tuples (depot id, filelist, manifest id) or None"""
    result = []
    combiner = defaultdict(list)

    for i in range(len(self.patch_list) - 1, 1, -1):
      patch_from = self.patch_list[i]
      patch_to = self.patch_list[i - 1]
      
      if patch_to['version'] >= selected_version and patch_to['version'] <= self.installed_version:
        # Check all changed depots for filelists
        for depot in patch_from["changed_depots"]:
          # Only care about relevant depots
          if depot['depot_id'] in relevant_depots:
            # Get filelist for current depot and version
            filelist = self.webhook.query_filelist(patch_from['version'], depot['depot_id'])

            # If one filelist is not documented,return None
            if filelist is None:
              return None

            combiner[depot['depot_id']].append({ 'filelist': filelist, 'manifest': depot['manifest_id'] })

    # Iterate each depot
    for depot in combiner.keys():
      merged = set()
      manifest = None

      # Merge all filelists for this depot into one
      for entry in combiner[depot]:
        merged.update(entry['filelist'].split("\n"))
        # Store latest manifest for this depot
        manifest = entry['manifest']

      # Sort filelist before appending?
      result.append({ 'depot': depot, 'filelist': "\n".join(merged), 'manifest': manifest })

    return result