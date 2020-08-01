import sys
import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import threading

import utils
import redirector
from logic import Logic, Languages

class App():
  def __init__(self):
    self.logic = Logic()
    self.patch_list = self.logic.get_patch_list()

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
    """Open a file dialog for the user to select the game folder and send the result to logic."""
    dir = tk.filedialog.askdirectory(mustexist=True)

    # askdirectory returns empty string on hitting cancel
    if dir != "":
      self.logic.set_game_dir(pathlib.Path(dir))

  def __patch(self):
    """Start patching the game with the downloaded files."""

    # Retrieve selected patch
    selected_patch = next((p for p in self.patch_list if p['title'] == self.selected_patch_title.get()), None)
    # Retrieve selected language
    selected_language = next((l.value for l in Languages if l.name == self.selected_language_name.get()), None)

    def work():
      self.logic.patch(self.ent_username.get(), self.ent_password.get(), selected_patch, selected_language)

    t = threading.Thread(target=work)
    t.start()

  def __restore(self):
    """Restores the game directory using the backed up files and downloaded files."""
    
    def work():
      self.logic.restore()
    
    t = threading.Thread(target=work)
    t.start()

if __name__ == '__main__':
  # @TODO Make GUI look nice
  # @TODO Generate file list to minimize download size
  # @TODO Test this thing a bit (Made a test run with 2FA and restoring and it worked)

  app = App()
  app.start()