from asyncio import CancelledError
import sys
import pathlib
import threading
import time

import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog
from queue import Empty, Queue

import redirector
from logic import Logic
from utils.path_utils import get_base_path


class App():
    def __init__(self, version_major: int, version_minor: int):
        self._ui_queue = Queue()
        self._ui_thread_id = threading.get_ident()
        self._worker = None
        self._close_requested = False
        self._closed = False

        self.version_major = version_major
        self.version_minor = version_minor

        self.logic = Logic(self._request_prompt)
        self.patch_list = list(reversed(self.logic.get_patch_list()))

        # Set up GUI
        self.window = tk.Tk()
        self.window.title(f"AoE2DE Patcher v{self.version_major}.{self.version_minor}")
        self.window.minsize(width=900, height=500)
        self.window.resizable(False, False)

        def on_closing():
            self._close_requested = True
            if self._worker is not None and self._worker.is_alive():
                self.logic.cancel_downloads()

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

        self.lbl_select_patch = ttk.Label(master=self.upper_frame, text="Target version")
        self.lbl_select_patch.grid(row=0, column=0, sticky="e")
        self.cmb_select_patch = ttk.Combobox(self.upper_frame, state="readonly", textvariable=self.selected_patch_title, values=[p for p in patch_titles])
        self.cmb_select_patch.current(0)    # Set default value
        self.cmb_select_patch.grid(row=0, column=1, sticky="ew")

        self.lbl_username = ttk.Label(master=self.upper_frame, text="Username")
        self.lbl_username.grid(row=2, column=0, sticky="e")
        self.ent_username = ttk.Entry(master=self.upper_frame)
        self.ent_username.grid(row=2, column=1, sticky="nesw")

        self.btn_patch = ttk.Button(master=self.upper_frame, text="Patch", command=self._patch)
        self.btn_patch.grid(row=0, column=5, sticky="nesw")

        self.btn_restore = ttk.Button(master=self.upper_frame, text="Restore", command=self._restore)
        self.btn_restore.grid(row=1, column=5, sticky="nesw")

        self.btn_game_dir = ttk.Button(master=self.upper_frame, text="Set Game directory", command=self._select_game_dir)
        self.btn_game_dir.grid(row=2, column=5, sticky="nesw")

        self.text_box = scrolledtext.ScrolledText(master=self.lower_frame, state="disabled")
        self.text_box.pack(expand=True, fill="both")

        # Redirect stdout to the text box
        sys.stdout = redirector.StdoutRedirector(self._enqueue_log)

    def start(self) -> None:
        """Start the application.
        """
        self._check_version()
        self.window.after(50, self._process_ui_queue)
        self.window.mainloop()

    def _select_game_dir(self) -> None:
        """Open a file dialog for the user to select the game folder and send the result to logic.
        """
        dir = tkinter.filedialog.askdirectory(mustexist=True)

        # askdirectory returns empty string on hitting cancel
        if dir != "":
            try:
                self.logic.set_game_dir(pathlib.Path(dir))
            except Exception as e:
                tkinter.messagebox.showerror(title="ERROR", message=str(e))

    def _check_version(self) -> None:
        """Check if there is a newer version of the tool available. Notify the user with a box if that is the case.
        """
        target_major, target_minor = self.logic.webhook.query_latest_version()

        if (self.version_major, self.version_minor) < (target_major, target_minor):
            print("There is a new version available at https://github.com/DJSchaffner/aoe2de_patcher")
            print("Please update because this version might no longer work!")

    def _patch(self) -> None:
        """Start patching the game with the downloaded files.
        """
        # Retrieve selected patch
        selected_index = self.cmb_select_patch.current()
        selected_patch = self.patch_list[selected_index] if selected_index >= 0 else None
        if selected_patch is None:
            tkinter.messagebox.showerror(title="ERROR", message="Could not retrieve selected patch version")
            return

        username = self.ent_username.get()

        def work():
            try:
                self._enqueue_ui(self._worker_started)
                self.logic.patch(username, selected_patch["version"])
                self._enqueue_ui(lambda: tkinter.messagebox.showinfo(message="Patching done"))
            except CancelledError:
                # Ignore error happening during cancellation
                pass
            except Exception as e:
                error_message = str(e)
                self._enqueue_ui(lambda: tkinter.messagebox.showerror(title="ERROR", message=error_message))
            finally:
                self._enqueue_ui(self._worker_finished)

        self._worker = threading.Thread(target=work)
        self._worker.start()

    def _restore(self) -> None:
        """Restores the game directory using the backed up files and downloaded files.
        """
        def work():
            try:
                self._enqueue_ui(self._worker_started)
                self.logic.restore()
                self._enqueue_ui(lambda: tkinter.messagebox.showinfo(message="Restore done"))
            except CancelledError:
                # Ignore error happening during cancellation
                pass
            except Exception as e:
                error_message = str(e)
                self._enqueue_ui(lambda: tkinter.messagebox.showerror(title="ERROR", message=error_message))
            finally:
                self._enqueue_ui(self._worker_finished)

        self._worker = threading.Thread(target=work)
        self._worker.start()

    def _enqueue_ui(self, callback) -> None:
        """Queue a callback for execution on the UI thread.

        Args:
            callback: The callback to execute on the UI thread
        """
        self._ui_queue.put(callback)

    def _process_ui_queue(self) -> None:
        """Execute callbacks queued for the UI thread.
        """
        while True:
            try:
                callback = self._ui_queue.get_nowait()
                callback()
            except Empty:
                break

        if self._close_requested and (self._worker is None or not self._worker.is_alive()):
            self._close_window()
        elif not self._closed:
            self.window.after(50, self._process_ui_queue)

    def _request_prompt(self, title: str, prompt: str, is_hidden: bool) -> str | None:
        """Requests to queue a prompt to the ui thread.

        Args:
            title (str): The prompt title
            prompt (str): The prompt text
            is_hidden (bool): If the entered text should be hidden

        Returns:
            str | None: The entered string or None if invalid or cancelled
        """
        def create_prompt(title: str, prompt: str, is_hidden: bool) -> str | None:
            temp = tkinter.Tk()
            temp.withdraw()

            try:
                return tkinter.simpledialog.askstring(
                    title=title,
                    prompt=prompt,
                    parent=temp,
                    show="*" if is_hidden else None
                )
            finally:
                temp.destroy()

        if threading.get_ident() == self._ui_thread_id:
            return create_prompt(title, prompt, is_hidden)

        response = []
        event = threading.Event()

        def show_prompt():
            response.append(create_prompt(title, prompt, is_hidden))
            event.set()

        self._enqueue_ui(show_prompt)
        event.wait()
        return response[0]

    def _enqueue_log(self, text: str) -> None:
        """Queue log text for display in the UI text box.

        Args:
            text (str): The text to append to the log
        """
        self._enqueue_ui(lambda: self._append_log(text))

    def _append_log(self, text: str) -> None:
        """Append text to the UI log text box.

        Args:
            text (str): The text to append
        """
        self.text_box.configure(state="normal")
        self.text_box.insert("end", text)
        self.text_box.configure(state="disabled")
        self.text_box.see("end")

    def _worker_started(self) -> None:
        self._disable_input()

    def _worker_finished(self) -> None:
        """Handle completion of a patch or restore worker.
        """
        self._worker = None
        if not self._close_requested:
            self._enable_input()

    def _close_window(self) -> None:
        """Save the UI log and close the application window.
        """
        if self._closed:
            return

        self._closed = True

        with open(get_base_path() / "log.txt", "w+") as file:
            file.write(self.text_box.get(1.0, "end-1c"))

        sys.stdout = sys.__stdout__
        self.window.destroy()

    def _disable_input(self) -> None:
        """Disables User input for certain Buttons / Entries.
        """
        self.cmb_select_patch.config(state="disabled")
        self.btn_patch.config(state="disabled")
        self.btn_restore.config(state="disabled")
        self.btn_game_dir.config(state="disabled")
        self.ent_username.config(state="disabled")

    def _enable_input(self) -> None:
        """Enables User input for certain Buttons / Entries.
        """
        self.cmb_select_patch.config(state="readonly")
        self.btn_patch.config(state="enabled")
        self.btn_restore.config(state="enabled")
        self.btn_game_dir.config(state="enabled")
        self.ent_username.config(state="enabled")
