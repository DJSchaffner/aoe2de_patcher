import os
import sys
import shutil
import traceback
import pathlib
from bs4 import BeautifulSoup
from getpass import getpass

import utils
from webhook import Webhook

class App:
  app_id = "813780"

  def __init__(self):
    # Check for installed dotnet
    if not (utils.check_dotnet()):
      print("DOTNET Core required but not found!")
      sys.exit()

    self.depots = ["813781", "813782", "813783", "813784"]
    self.manifests = ["620891448408726573", "8112931571790254060", "8481199905487006177", "5123643355926127017"]
    self.webhook = Webhook()

    self.game_path = pathlib.Path(input("Enter Path to AoE2DE: "))
    self.download_path = utils.base_path() / "download"
    self.backup_path = utils.base_path() / "backup"

    # Remove previous download / backup folder if it exists
    # Create empty folders afterwards
    if self.download_path.exists():
      shutil.rmtree(self.download_path.absolute())
    self.download_path.mkdir()
    
    if self.backup_path.exists():
      shutil.rmtree(self.backup_path.absolute())
    self.backup_path.mkdir()

    self.username = input("Username: ")
    self.password = getpass() 

    #self.__get_patch_changes(self.__get_patch_list()[1][1])

  def download_patch(self):  
    # Get all necessary depots
    for depot, manifest in zip(self.depots, self.manifests):
      self.__download_depot(depot, manifest)

  def patch(self):
    # Copy downloaded files into game path
    shutil.copytree(self.download_path.absolute(), self.game_path.absolute(), dirs_exist_ok = True)

  # Backup game folder and zip it up in current directory
  def backup(self):
    changed_file_list = list(set(os.listdir(self.game_path.absolute())).intersection(set(os.listdir(self.download_path.absolute()))))

    # Copy all files
    for file in changed_file_list:
      if pathlib.Path(self.game_path / file).is_dir():
        shutil.copytree((self.game_path / file).absolute(), (self.backup_path / file).absolute())
      else:
        shutil.copy((self.game_path / file).absolute(), (self.backup_path / file).absolute())

  # Placeholder function to restore game from backup
  def restore(self):
    changed_file_list = list(set(os.listdir(self.game_path.absolute())).intersection(set(os.listdir(self.download_path.absolute()))))
    print(changed_file_list)

  # Download depot from steam
  def __download_depot(self, depot_id, manifest_id):
    depot_downloader = utils.resource_path("DepotDownloader/DepotDownloader.dll").absolute()
    os.system(f"dotnet {depot_downloader} -app {self.app_id} -depot {depot_id} -manifest {manifest_id} -username {self.username} -password {self.password} -dir download")

  # Get a list of all patches
  def __get_patch_list(self):
    result = []

    soup = BeautifulSoup(self.webhook.query_patch_list(self.app_id).content, "html.parser")
    tbody = soup.find("tbody")
    
    for tr in tbody.findAll("tr"):
      tds = tr.findAll("td")
      result.append((tds[0].string, tds[4].string))
    return result

  # Get the changes for a specific patch
  # Returns a list of Tuples [(Date, ID), ...]
  def __get_patch_changes(self, patch_id):
    result = []

    soup = BeautifulSoup(self.webhook.query_patch(patch_id).content, "html.parser")

    div = soup.find("div", {"class" : "depot-history"})

    inner_divs = div.findAll("div")[1:]

    for depot_div in inner_divs:
      # @TODO Somehow execute the javascript on the page to load the change history
      print(depot_div.string)

    return result

if __name__ == '__main__':
  # @TODO Make a GUI for this whole thing
  # @TODO Generate file list to minimize download size
  # @TODO Grab manifest IDs from steamdb automatically
  # @TODO Grab Update list from steamdb automatically
  # @TODO Add restore functionality
  # @TODO Improve backup mechanism
  try:
    app = App()

    print("Starting download of files")
    app.download_patch()
    print("Finished downloading files!")

    print("Starting backup of AoE2DE folder")
    app.backup()
    print("Finished backup!")

    print("Copying downloaded files")
    app.patch()
    print("Done!")

    # Wait for user input to close
    input("Press enter to exit...")
  except BaseException:
    print(traceback.format_exc())
    input("")