import os
import sys
import shutil
import utils
from getpass import getpass

def check_dotnet():
  return not (shutil.which("dotnet") == None)

# Backup game folder and zip it up in current directory
def backup(game_path, download_path, backup_path):
  changed_file_list = list(set(os.listdir(game_path)).intersection(set(os.listdir(download_path))))

  for file in changed_file_list:
    if os.path.isdir(f"{game_path}\\{file}"):
      shutil.copytree(f"{game_path}\\{file}", f"{backup_path}\\{file}")
    else:
      shutil.copy(f"{game_path}\\{file}", f"{backup_path}\\{file}")

def restore(game_path, download_path, backup_path):
  changed_file_list = list(set(os.listdir(game_path)).intersection(set(os.listdir(download_path))))
  print(changed_file_list)

# Download depot from steam
def get_depot(depot_id, manifest_id, username, password):
  depot_downloader = utils.resource_path("res/DepotDownloader/DepotDownloader.dll")
  os.system(f"dotnet {depot_downloader} -app {app_id} -depot {depot_id} -manifest {manifest_id} -username {username} -password {password} -dir download")

if __name__ == '__main__':
  # @TODO Make a GUI for this whole thing
  # @TODO Generate file list to minimize download size
  # @TODO Grab manifest IDs from steamdb automatically
  # @TODO Remove previous download dir before process starts
  # @TODO Improve backup mechanism
  app_id = "813780"
  depots = ["813781", "813782", "813783", "813784"]
  manifests = ["620891448408726573", "8112931571790254060", "8481199905487006177", "5123643355926127017"]
  download_path = utils.resource_path("download")
  backup_path = utils.resource_path("backup")

  # Check for installed dotnet
  if not (check_dotnet()):
    print("DOTNET Core required but not found!")
    sys.exit()

  # Get user input
  game_path = input("Enter Path to AoE2DE: ")
  username = input("Username: ")
  password = getpass()

  # Remove previous download / backup folder if it exists
  # Create empty folders afterwards
  if (os.path.exists(download_path)):
    shutil.rmtree(download_path)
  os.mkdir(download_path)

  if (os.path.exists(backup_path)):
    shutil.rmtree(backup_path)
  os.mkdir(backup_path)

  # Get all necessary depots
  for depot, manifest in zip(depots, manifests):
    get_depot(depot, manifest, username, password)

  # Backup game folder
  print("Starting backup of AoE2DE folder")
  backup(game_path, download_path, backup_path)
  print("Finished backup!")

  # Move downloaded files to game directory and override files
  print("Copying downloaded files")
  shutil.copytree(download_path, game_path)
  print("Done!")

  # Wait for user input to close
  input("Press enter to exit...")