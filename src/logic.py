import sys
import os
import pathlib
import shutil
from enum import IntEnum

import pexpect
import pexpect.popen_spawn
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
    self.download_dir = utils.base_path() / "download"
    self.backup_dir = utils.base_path() / "backup"
    self.patch_list = self.webhook.query_patch_list(self.app_id)
    self.depot_list = self.__get_depot_list()

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

    # Always true
    if success:
      print("Downloading patch")
      success = success and self.__download_patch(username, password, patch, language)

    if success:
      print("Starting backup")
      success = success and self.__backup()

    if success:
      print("Patching files")
      success = success and self.__move_patch()

    if success:
      print("DONE!")
    else:
      print("Could not patch!")

  def restore(self):
    """Restores the game directory using the backed up files and downloaded files."""

    if not self.backup_dir.exists():
      print("Backup directory doesn't exist")
      return

    if len(os.listdir(self.backup_dir.absolute())) == 0:
      print("No backup stored")
      return
    
    backup_file_list = list(os.listdir(self.backup_dir.absolute()))
    download_file_list = list(os.listdir(self.download_dir.absolute()))

    # Remove added files from the path
    print("Removing patched files")
    for file in download_file_list:
      utils.remove_file_or_dir(self.game_dir, file)
    print("Finished removing patched files")

    # Copy backed up files to game path again
    print("Restoring backup")
    for file in backup_file_list:
      utils.copy_file_or_dir(self.backup_dir, self.game_dir, file)
    print("Finished restoring backup")
    print("DONE!")

  def set_game_dir(self, dir: pathlib.Path):
    """Tries to set the game directory, if succesful return True. Otherwise return False"""

    if "AoE2DE_s.exe" in os.listdir(dir):
      self.game_dir = dir
      print(f"Game directory set to: {dir.absolute()}")
      return True

    print("Invalid game directory")
    return False

  def get_patch_list(self):
    """Returns the patch list"""

    return self.patch_list

  def __download_patch(self, username: str, password: str, patch: dict, language: Languages):  
    """Download the given patch in a language using the steam account credentials."""

    # dotnet is required to proceed
    if not (utils.check_dotnet()):
      print("DOTNET Core required but not found!")
      return False
    
    update_list = []    
    
    # Remove previous download folder if it exists
    # Create empty folders afterwards
    if self.download_dir.exists():
      shutil.rmtree(self.download_dir.absolute())
    self.download_dir.mkdir()
    
    # Loop all depots and insert necessary ones with the latest version to the list of updates
    # @TODO Only add the depots that NEED to be updated depending on which version is currently installed
    for depot in self.depot_list:
      # Skip depots that are being ignored
      if  ( (not (depot in self.ignored_depots)) and 
            ((not (depot in self.language_depots)) or (self.language_depots[language] == depot)) ):

        manifests = self.webhook.query_manifests(depot)

        # Discard empty manifest lists
        if len(manifests) > 0:
          update_list.append({ 'depot' : depot, 'manifest' : next((m for m in manifests if m['date'] <= patch['date']), None) })      

    # Loop all necessary updates
    for element in update_list:
      if not self.__download_depot(username, password, element['depot'], element['manifest']['id']):
        return False

    return True

  def __move_patch(self):
    """Move downloaded patch files to game directory"""

    shutil.copytree(self.download_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok = True)
    return True

  def __backup(self):
    """Backup game folder and in current directory."""

    # Remove previous backup folder if it exists
    # Create empty folders afterwards
    if self.backup_dir.exists():
      shutil.rmtree(self.backup_dir.absolute())
    self.backup_dir.mkdir()

    changed_file_list = list(set(os.listdir(self.game_dir.absolute())).intersection(set(os.listdir(self.download_dir.absolute()))))

    # Copy all files
    for file in changed_file_list:
      utils.copy_file_or_dir(self.game_dir, self.backup_dir, file)

    return True

  def __download_depot(self, username: str, password: str, depot_id, manifest_id):
    """Download a specific depot using the manifest id from steam using the given credentials."""

    success = False
    depot_downloader = str(utils.resource_path("DepotDownloader/DepotDownloader.dll").absolute())
    args = ["dotnet", depot_downloader, "-app", str(self.app_id), "-depot", str(depot_id), "-manifest", str(manifest_id), "-username", username, "-password", password, "-dir download"]

    try:
      p = pexpect.popen_spawn.PopenSpawn(" ".join(args), encoding="utf-8")
      p.logfile_read = sys.stdout

      responses = [
        "result: OK",
        "Please enter .*: ",
        pexpect.EOF
      ]

      # Default timeout in seconds
      timeout = 15
      i = p.expect(responses, timeout=timeout)

      # Success
      if i == 0:
        success = True

      # Code required
      elif i == 1:
        # Open popup for 2FA Code
        code = tkinter.simpledialog.askstring(title="Code", prompt="Please enter your 2FA login code")
        # Cancel was clicked
        if code is None:
          raise ConnectionError("Invalid authentication code")
        # Code was entered
        else:
          p.sendline(code)

          if p.expect(responses, timeout=timeout) == 1:
            raise ConnectionError("Invalid authentication code")
          else:
            success = True

      # Error
      elif i == 2:
        raise ConnectionError("Error logging into account")

      # Wait for program to finish
      p.expect(pexpect.EOF)
    except pexpect.exceptions.TIMEOUT as e:
      print("Error waiting for DepotDownloader to start")
    except ConnectionError as e:
      print(e)

    return success

  def __get_depot_list(self):
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