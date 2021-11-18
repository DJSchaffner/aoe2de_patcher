import sys
import pathlib
import threading
import time

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog

import redirector
from logic import Logic, Languages

class App():
  def __init__(self):
    self.logic = Logic()
    self.patch_list = list(reversed(self.logic.get_patch_list()))

    self.version = 1.30

    # Set up GUI
    self.window = tk.Tk()
    self.window.title("AoE2DE Patcher")
    self.window.minsize(width=900, height=500)
    self.window.resizable(0, 0)

    def on_closing():
      self.logic.cancel_downloads()
      self.window.destroy()

    self.window.protocol("WM_DELETE_WINDOW", on_closing)
    
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
    
    patch_titles = [f"{p['version']} - {time.strftime('%d/%m/%Y', time.gmtime(p['date']))}" for p in self.patch_list]

    self.lbl_select_patch = ttk.Label(master=self.upper_frame, text="Version")
    self.lbl_select_patch.grid(row=0, column=0, sticky="e")  
    self.opt_select_patch = ttk.OptionMenu(self.upper_frame, self.selected_patch_title, patch_titles[0], *[p for p in patch_titles])
    self.opt_select_patch.grid(row=0, column=1, sticky="w")

    self.selected_language_name = tk.StringVar()
    self.lbl_select_language = ttk.Label(master=self.upper_frame, text="Language")
    self.lbl_select_language.grid(row=1, column=0, sticky="e")  
    self.opt_select_language = ttk.OptionMenu(self.upper_frame, self.selected_language_name, Languages.EN.name, *[l.name for l in Languages])
    self.opt_select_language.grid(row=1, column=1, sticky="w")

    self.btn_patch = ttk.Button(master=self.upper_frame, text="Patch", command=self._patch)
    self.btn_patch.grid(row=0, column=5, sticky="nesw")

    self.btn_restore = ttk.Button(master=self.upper_frame, text="Restore", command=self._restore)
    self.btn_restore.grid(row=1, column=5, sticky="nesw")

    self.btn_game_dir = ttk.Button(master=self.upper_frame, text="Set Game directory", command=self._select_game_dir)
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
    """Start the application.
    """
    self._check_version()
    self.window.mainloop()

  def _select_game_dir(self):
    """Open a file dialog for the user to select the game folder and send the result to logic.
    """
    dir = tk.filedialog.askdirectory(mustexist=True)

    # askdirectory returns empty string on hitting cancel
    if dir != "":
      self.logic.set_game_dir(pathlib.Path(dir))

  def _check_version(self):
    """Check if there is a newer version of the tool available. Notify the user with a box if that is the case.
    """
    if self.version < self.logic.webhook.query_latest_version():
      print("There is a new version available at https://github.com/DJSchaffner/aoe2de_patcher")

  def _patch(self):
    """Start patching the game with the downloaded files.
    """
    # Retrieve selected patch
    selected_patch = next((p for p in self.patch_list if str(p['version']) in self.selected_patch_title.get()), None)
    # Retrieve selected language
    selected_language = next((l.value for l in Languages if l.name == self.selected_language_name.get()), None)

    def work():
      self._disable_input()
      self.logic.patch(self.ent_username.get(), self.ent_password.get(), selected_patch, selected_language)
      self._enable_input()

    t = threading.Thread(target=work)
    t.start()

  def _restore(self):
    """Restores the game directory using the backed up files and downloaded files.
    """
    def work():
      self._disable_input()
      self.logic.restore()
      self._enable_input()
    
    t = threading.Thread(target=work)
    t.start()

  def _disable_input(self):
    """Disables User input for certain Buttons / Entries.
    """
    self.opt_select_patch.config(state="disabled")
    self.opt_select_language.config(state="disabled")
    self.btn_patch.config(state="disabled")
    self.btn_restore.config(state="disabled")
    self.btn_game_dir.config(state="disabled")
    self.ent_username.config(state="disabled")
    self.ent_password.config(state="disabled")

  def _enable_input(self):
    """Enables User input for certain Buttons / Entries.
    """
    self.opt_select_patch.config(state="enabled")
    self.opt_select_language.config(state="enabled")
    self.btn_patch.config(state="enabled")
    self.btn_restore.config(state="enabled")
    self.btn_game_dir.config(state="enabled")
    self.ent_username.config(state="enabled")
    self.ent_password.config(state="enabled")

if __name__ == '__main__':
  app = App()
  app.start()