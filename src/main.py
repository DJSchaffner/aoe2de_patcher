import os
import sys
import shutil
import utils
from getpass import getpass

def check_dotnet():
  return not (shutil.which("dotnet") == None)

# Backup game folder and zip it up in current directory
def backup(game_path):
  shutil.make_archive("backup", "zip", utils.resource_path(game_path), ".", )

# Download depot from steam
def get_depot(depot_id, manifest_id, username, password):
  depot_downloader = utils.resource_path("res/DepotDownloader/DepotDownloader.dll")
  os.system(f"dotnet {depot_downloader} -app {app_id} -depot {depot_id} -manifest {manifest_id} -username {username} -password {password} -dir download")

if __name__ == '__main__':
  # @TODO Make a GUI for this whole thing
  # @TODO Check if Dot.NET core is installed
  # @TODO Generate file list to minimize download size
  # @TODO Grab manifest IDs from steamdb automatically
  # @TODO Remove previous download dir before process starts
  app_id = "813780"
  depots = ["813781", "813782", "813783", "813784"]
  manifests = ["620891448408726573", "8112931571790254060", "8481199905487006177", "5123643355926127017"]
  download_path = utils.resource_path("download")

  if not (check_dotnet()):
    print("DOTNET Core required but not found!")
    sys.exit()

  # Get user input
  game_path = input("Enter Path to AoE2DE: ")
  username = input("Username: ")
  password = getpass()

  # Backup game folder
  print("Starting backup of AoE2DE folder")
  backup(game_path)
  print("Finished backup!")

  # Get all necessary depots
  for depot, manifest in zip(depots, manifests):
    get_depot(depot, manifest, username, password)

  # Move downloaded files to game directory and override files
  print("Copying downloaded files")
  shutil.copytree(download_path, game_path)
  print("Done!")

  input("Press enter to exit...")