import os
import sys
import subprocess
import re
from queue import Queue

import time
import tkinter
import tkinter.simpledialog

import utils


class DepotDownloaderHelper:
    def __init__(self):
        self.process_queue = Queue()

    def execute(self, options: list):
        """Execute the DepotDownloader with the given options as arguments. Return True if successful.

        Args:
            options (list): A list of options that will be passed to DepotDownloader directly

        Raises:
            ConnectionError: If there was an error during authentication
        """
        args = ["dotnet", str(utils.resource_path('DepotDownloader/DepotDownloader.dll').absolute())] + options

        # Spawn process and store in queue
        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        self.process_queue.put(process)

        # Set read mode to non-blocking for process to handle prompts without newlines
        assert process.stdout is not None
        os.set_blocking(process.stdout.fileno(), False)

        # Wait a bit so the program can produce output
        # TODO: Find a better solution for this
        time.sleep(1)

        try:
            self._handle_authentication(process)

            # Wait for program to finish
            process.wait()
        except ConnectionError:
            raise
        finally:
            # Remove process from queue after working with it
            self.process_queue.get()
            if process.poll() is None:
                process.terminate()

    def cancel_downloads(self):
        """Performs cleanup for logic object.
        """
        for process in self.process_queue.queue:
            process.terminate()

    def _handle_authentication(self, process: subprocess.Popen):
        """Handle interactive authentication flow

        Args:
            process (subprocess.Popen): The process

        Raises:
            ConnectionError: If there was an error during authentication
        """
        assert process.stdout is not None
        assert process.stdin is not None

        responses = [
            r"STEAM GUARD! Please enter .*: ",
            r"STEAM GUARD! Use .*\.\.\.",
            r"Enter account password.*: ",
            r"result: OK",
            r"Error: InitializeSteam failed"
        ]

        while True:
            line = process.stdout.readline()
            if not line:  # EOF
                break

            # Print output in real-time
            sys.stdout.write(line)
            sys.stdout.flush()

            # Check patterns
            response = -1
            for i, pattern in enumerate(responses):
                if re.search(pattern, line):
                    response = i
                    break

            # Handle responses
            if response == 0:  # Code required
                code = self._open_temp_prompt("Code", "Please enter your 2FA login code", False)

                if code is None:
                    raise ConnectionError("Invalid authentication code")

                process.stdin.write(code.upper() + '\n')
                process.stdin.flush()

                # Check if code was accepted
                next_line = process.stdout.readline()
                sys.stdout.write(next_line)
                sys.stdout.flush()

                if next_line and re.search(responses[0], next_line):
                    raise ConnectionError("Invalid authentication code")

            elif response == 1:  # Steam Guard app
                pass  # Just continue

            elif response == 2:  # Password prompt
                password = self._open_temp_prompt("Code", "Please enter your password", True)

                if password is None:
                    raise ConnectionError("Invalid password")

                process.stdin.write(password + '\n')
                process.stdin.flush()
                self._handle_authentication(process)
                break

            elif response == 3:  # Success
                break

            elif response == 4:  # Error
                raise ConnectionError("Could not login to steam account")

    def _open_temp_prompt(self, title: str, prompt: str, is_hidden: bool) -> str | None:
        """Opens a prompt widget with the requested title and prompt to enter information

        Args:
            title (str): The prompt window title
            prompt (str): The prompt window text
            is_hidden (bool): Flag to hide user input

        Returns:
            str | None: The entered string or None if invalid or cancelled
        """
        temp = tkinter.Tk()
        temp.withdraw()
        response = tkinter.simpledialog.askstring(
            title=title,
            prompt=prompt,
            parent=temp,
            show="*" if is_hidden else None
        )
        temp.destroy()

        return response
