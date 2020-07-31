import os
import sys
import shutil
import traceback
import pathlib
from getpass import getpass
from steam.client import SteamClient
from enum import IntEnum
import datetime
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.simpledialog
import pexpect
import pexpect.popen_spawn

import utils
import redirector
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

class App():
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
    # dotnet is required to proceed
    if not (utils.check_dotnet()):
      print("DOTNET Core required but not found!")
      sys.exit()

    # Set up some variables
    self.webhook = Webhook()
    self.download_dir = utils.base_path() / "download"
    self.backup_dir = utils.base_path() / "backup"
    self.patch_list = self.webhook.query_patch_list(self.app_id)

    # Set up GUI
    self.window = tk.Tk()
    self.window.title("AoE2DE Patch Reverter")
    self.window.minsize(width=700, height=500)
    self.window.resizable(0, 0)
    
    self.upper_frame = tk.Frame(master=self.window)
    self.upper_frame.pack(side="top", expand=True, fill="both", padx=10, pady=(10, 5))
    self.upper_frame.columnconfigure(0, weight=1)
    self.upper_frame.columnconfigure(1, weight=1)
    self.upper_frame.columnconfigure(2, weight=1)
    self.upper_frame.columnconfigure(3, weight=1)
    self.upper_frame.columnconfigure(4, weight=1)
    self.upper_frame.columnconfigure(5, weight=1)
    self.upper_frame.rowconfigure(0, weight=1)
    self.upper_frame.rowconfigure(1, weight=1)
    self.upper_frame.rowconfigure(2, weight=1)

    self.lower_frame = tk.Frame(master=self.window)
    self.lower_frame.pack(side="bottom", expand=True, fill="both", padx=10, pady=(5, 10))

    self.selected_patch_title = tk.StringVar()  
    self.lbl_select_patch = ttk.Label(master=self.upper_frame, text="Version")
    self.lbl_select_patch.grid(row=0, column=0, sticky="e")  
    self.opt_select_patch = ttk.OptionMenu(self.upper_frame, self.selected_patch_title, self.patch_list[0]['title'], *[p['title'] for p in self.patch_list])
    self.opt_select_patch.grid(row=0, column=1, sticky="w")

    self.selected_language_name = tk.StringVar()
    self.lbl_select_language = ttk.Label(master=self.upper_frame, text="Language")
    self.lbl_select_language.grid(row=1, column=0, sticky="e")  
    self.opt_select_language = ttk.OptionMenu(self.upper_frame, self.selected_language_name, Languages.EN.name, *[l.name for l in Languages])
    self.opt_select_language.grid(row=1, column=1, sticky="w")

    self.btn_patch = ttk.Button(master=self.upper_frame, text="Patch", command=self.__patch)
    self.btn_patch.grid(row=0, column=5, sticky="nesw")

    self.btn_restore = ttk.Button(master=self.upper_frame, text="Restore", command=self.__restore)
    self.btn_restore.grid(row=1, column=5, sticky="nesw")

    self.btn_game_dir = ttk.Button(master=self.upper_frame, text="Set Game directory", command=self.__select_game_dir)
    self.btn_game_dir.grid(row=2, column=5, sticky="nesw")

    self.lbl_username = ttk.Label(master=self.upper_frame, text="Username")
    self.lbl_username.grid(row=2, column=0, sticky="e")
    self.ent_username = ttk.Entry(master=self.upper_frame)
    self.ent_username.grid(row=2, column=1, sticky="nesw")

    self.lbl_password = ttk.Label(master=self.upper_frame, text="Password")
    self.lbl_password.grid(row=2, column=2, sticky="e")
    self.ent_password = ttk.Entry(master=self.upper_frame, show="*")
    self.ent_password.grid(row=2, column=3, sticky="nesw")

    self.text_box = tk.Text(master=self.lower_frame, state="disabled")
    self.text_box.pack(expand=True, fill="both")

    # Redirect stdout to the text box
    sys.stdout = redirector.StdoutRedirector(self.text_box)

  def start(self):
    """Start the application."""

    self.window.mainloop()

  def __select_game_dir(self):
    """Open a file dialog for the user to select the game folder."""
    # @TODO validate its actually the AoE directory (Check for aoe exe)
    self.game_dir = pathlib.Path(tk.filedialog.askdirectory())

  def __download_patch(self):  
    """Download the __patch that has been set for the app."""
    
    depots = self.__get_depot_list()
    update_list = []

    # Retrieve selected patch
    selected_patch = next((p for p in self.patch_list if p['title'] == self.selected_patch_title.get()), None)
    # Retrieve selected language
    selected_language = next((l.value for l in Languages if l.name == self.selected_language_name.get()), None)
    
    # Remove previous download folder if it exists
    # Create empty folders afterwards
    if self.download_dir.exists():
      shutil.rmtree(self.download_dir.absolute())
    self.download_dir.mkdir()
    
    # Loop all depots and insert necessary ones with the latest version to the list of updates
    # @TODO Only add the depots that NEED to be updated depending on which version is currently installed
    for depot in depots:
      # Skip depots that are being ignored
      if  ( (not (depot in self.ignored_depots)) and 
            ((not (depot in self.language_depots)) or (self.language_depots[selected_language] == depot)) ):

        manifests = self.webhook.query_manifests(depot)

        # Discard empty manifest lists
        if len(manifests) > 0:
          update_list.append({ 'depot' : depot, 'manifest' : next((m for m in manifests if m['date'] <= selected_patch['date']), None) })      

    # Loop all necessary updates
    for element in update_list:
      if not self.__download_depot(element['depot'], element['manifest']['id']):
        return False

    return True

  def __move_patch(self):
    """Move downloaded patch files to game directory"""

    shutil.copytree(self.download_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok = True)
    return True

  def __patch(self):
    """Start patching the game with the downloaded files."""

    success = True

    # Check some stuff
    if not hasattr(self, "game_dir"):
      print("Please select a game directory")
      return

    if self.ent_username.get() == "":
      print("Please enter a username")
      return

    if self.ent_password.get() == "":
      print("Please enter a password")
      return

    # Always true
    if success:
      print("Downloading patch")
      success = success and self.__download_patch()

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

  def __restore(self):
    """Restores the game directory using the backed up files and downloaded files."""
    
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

  def __download_depot(self, depot_id, manifest_id):
    """Download a specific depot using the manifest id from steam."""

    success = False
    depot_downloader = str(utils.resource_path("DepotDownloader/DepotDownloader.dll").absolute())
    args = ["dotnet", depot_downloader, "-app", str(self.app_id), "-depot", str(depot_id), "-manifest", str(manifest_id), "-username", str(self.ent_username.get()), "-password", str(self.ent_password.get()), "-dir download"]

    try:
      p = pexpect.popen_spawn.PopenSpawn(" ".join(args), encoding="utf-8")
      p.logfile_read = sys.stdout

      responses = [
        "result: OK",
        "Error",
        "Please enter .*: "
      ]

      # Default timeout in seconds
      timeout = 15
      i = p.expect(responses, timeout)
      sys.stdout.flush()

      # Success
      if i == 0:
        success = True
      # Error
      elif i == 1:
        raise ConnectionError("Error logging into account")
      # Code required
      elif i == 2:
        # Open popup for 2FA Code
        code = tk.simpledialog.askstring(title="Code", prompt="Please enter your login code (2FA / Email)")
        p.sendline(code)

        if p.expect(responses, timeout=30) == 1:
          success = False
        else:
          raise ConnectionError("Invalid authentication code")

      p.wait()
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

if __name__ == '__main__':
  # @TODO Make GUI look nice
  # @TODO Generate file list to minimize download size
  # @TODO Test this thing a bit
  app = App()
  app.start()