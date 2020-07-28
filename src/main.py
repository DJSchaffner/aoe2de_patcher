import os
import sys
import shutil
import utils
import traceback
import pathlib
from getpass import getpass

# Check if dotnet is available
def check_dotnet():
  return not (shutil.which("dotnet") == None)

# Backup game folder and zip it up in current directory
def backup(game_path, download_path, backup_path):
  changed_file_list = list(set(os.listdir(game_path.absolute())).intersection(set(os.listdir(download_path.absolute()))))

  # Copy all files
  for file in changed_file_list:
    if pathlib.Path(game_path / file).is_dir():
      shutil.copytree((game_path / file).absolute(), (backup_path / file).absolute())
    else:
      shutil.copy((game_path / file).absolute(), (backup_path / file).absolute())

# Placeholder function to restore game from backup
def restore(game_path, download_path, backup_path):
  changed_file_list = list(set(os.listdir(game_path.absolute())).intersection(set(os.listdir(download_path.absolute()))))
  print(changed_file_list)

# Download depot from steam
def get_depot(depot_id, manifest_id, username, password):
  depot_downloader = utils.resource_path("DepotDownloader/DepotDownloader.dll").absolute()
  os.system(f"dotnet {depot_downloader} -app {app_id} -depot {depot_id} -manifest {manifest_id} -username {username} -password {password} -dir download")

if __name__ == '__main__':
  # @TODO Make a GUI for this whole thing
  # @TODO Generate file list to minimize download size
  # @TODO Grab manifest IDs from steamdb automatically
  # @TODO Grab Update list from steamdb automatically
  # @TODO Add restore functionality
  # @TODO Improve backup mechanism
  try:
    app_id = "813780"
    depots = ["813781", "813782", "813783", "813784"]
    manifests = ["620891448408726573", "8112931571790254060", "8481199905487006177", "5123643355926127017"]
    download_path = utils.base_path() / "download"
    backup_path = utils.base_path() / "backup"

    # Check for installed dotnet
    if not (check_dotnet()):
      print("DOTNET Core required but not found!")
      sys.exit()

    # Get user input
    game_path = pathlib.Path(input("Enter Path to AoE2DE: "))
    username = input("Username: ")
    password = getpass()

    # Remove previous download / backup folder if it exists
    # Create empty folders afterwards
    if download_path.exists():
      shutil.rmtree(download_path.absolute())
    download_path.mkdir()
    
    if backup_path.exists():
      shutil.rmtree(backup_path.absolute())
    backup_path.mkdir()

    # Get all necessary depots
    for depot, manifest in zip(depots, manifests):
      get_depot(depot, manifest, username, password)

    # Backup game folder
    print("Starting backup of AoE2DE folder")
    backup(game_path, download_path, backup_path)
    print("Finished backup!")

    # Move downloaded files to game directory and override files
    print("Copying downloaded files")
    shutil.copytree(download_path.absolute(), game_path.absolute(), dirs_exist_ok = True)
    print("Done!")

    # Wait for user input to close
    input("Press enter to exit...")
  except BaseException:
    print(traceback.format_exc())
    input("")