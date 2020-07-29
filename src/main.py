import os
import sys
import shutil
import traceback
import pathlib
from getpass import getpass
from steam.client import SteamClient
from enum import IntEnum
import datetime

import utils
from webhook import Webhook

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

class App:
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
    1022225, # ES
  ]

  def __init__(self):
    # dotnet is required to proceed
    if not (utils.check_dotnet()):
      print("DOTNET Core required but not found!")
      sys.exit()

    self.webhook = Webhook()
    self.patch_list = self.webhook.query_patch_list(self.app_id)
    self.selected_patch = self.patch_list[0]
    self.selected_language = Languages.EN

    self.game_path = pathlib.Path(input("Enter Path to AoE2DE: "))
    self.download_path = utils.base_path() / "download"
    self.backup_path = utils.base_path() / "backup"

    self.username = input("Username: ")
    self.password = getpass()

  def download_patch(self):  
    """Download the patch that has been set for the app."""
    
    depots = self.__get_depot_list()
    update_list = []
    
    # Remove previous download folder if it exists
    # Create empty folders afterwards
    if self.download_path.exists():
      shutil.rmtree(self.download_path.absolute())
    self.download_path.mkdir()
    
    # Loop all depots and insert necessary ones with the latest version to the list of updates
    # @TODO Only add the depots that NEED to be updated depending on which version is currently installed
    for depot in depots:
      # Skip depots that are being ignored
      if  ( (not (depot in self.ignored_depots)) and 
            ((not (depot in self.language_depots)) or (self.language_depots[self.selected_language] == depot)) ):

        manifests = self.webhook.query_manifests(depot)

        # Discard empty manifest lists
        if len(manifests) > 0:
          update_list.append({ 'depot' : depot, 'manifest' : next((m for m in manifests if m['date'] <= self.selected_patch['date']), None) })      

    # Loop all necessary updates
    for element in update_list:
      #print(f"depot: {element['depot']} - manifest: {element['manifest']}")
      self.__download_depot(element['depot'], element['manifest']['id'])

  def patch(self):
    """Start patching the game with the downloaded files."""

    shutil.copytree(self.download_path.absolute(), self.game_path.absolute(), dirs_exist_ok = True)

  def backup(self):
    """Backup game folder and in current directory."""

    # Remove previous backup folder if it exists
    # Create empty folders afterwards
    if self.backup_path.exists():
      shutil.rmtree(self.backup_path.absolute())
    self.backup_path.mkdir()

    changed_file_list = list(set(os.listdir(self.game_path.absolute())).intersection(set(os.listdir(self.download_path.absolute()))))

    # Copy all files
    for file in changed_file_list:
      utils.copy_file_or_dir(self.game_path, self.backup_path, file)

  def restore(self):
    """Restores the game directory using the backed up files and downloaded files."""
    
    backup_file_list = list(os.listdir(self.backup_path.absolute()))
    download_file_list = list(os.listdir(self.download_path.absolute()))

    # Remove added files from the path
    for file in download_file_list:
      utils.remove_file_or_dir(self.game_path, file)

    # Copy backed up files to game path again
    for file in backup_file_list:
      utils.copy_file_or_dir(self.backup_path, self.game_path, file)

  def __download_depot(self, depot_id, manifest_id):
    """Download a specific depot using the manifest id from steam."""

    depot_downloader = utils.resource_path("DepotDownloader/DepotDownloader.dll").absolute()
    os.system(f"dotnet {depot_downloader} -app {self.app_id} -depot {depot_id} -manifest {manifest_id} -username {self.username} -password {self.password} -dir download")

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

if __name__ == '__main__':
  # @TODO Make a GUI for this whole thing
  # @TODO Generate file list to minimize download size
  # @TODO Grab Update list from steamdb automatically
  # @TODO Add restore functionality
  # @TODO Improve backup mechanism
  try:
    app = App()
    action = 0

    while True:
      while not (action in [1, 2, 3]):
        print("1: Patch game")
        print("2: Restore game")
        print("3: Exit")
        action = int(input("Selection: "))

      print()

      if action == 1:
        print("Starting download of files")
        #app.download_patch()
        print("Finished downloading files!")

        print("Starting backup of AoE2DE folder")
        app.backup()
        print("Finished backup!")

        print("Copying downloaded files")
        app.patch()
        print("Finished copying files!")
        action = 0
      elif action == 2:
        print("Restoring directory")
        app.restore()
        print("Finished restoring directory!")
        action = 0
      elif action == 3:
        break

      print()

    # Wait for user input to close
    input("Press enter to exit...")
  except BaseException:
    print(traceback.format_exc())
    input("")