import os
import sys
import subprocess
import re
from queue import Queue
from enum import Enum

import time
import tkinter
import tkinter.simpledialog

import utils


class ProcessState(Enum):
    UNKNOWN = 0
    FINISHED = 1
    AUTH_SUCCESS = 2
    AUTH_FAILED = 3
    AUTH_PASSWORD_REQUIRED = 4
    AUTH_STEAM_GUARD = 5
    AUTH_TWO_FACTOR = 6


class DepotDownloaderHelper:
    def __init__(self):
        self.process_queue = Queue()

    def execute(self, options: list) -> None:
        """Execute the DepotDownloader with the given options as arguments.

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

        try:
            self._handle_process(process)
        except ConnectionError:
            raise
        finally:
            # Remove process from queue after working with it
            self.process_queue.get()
            if process.poll() is None:
                process.terminate()

    def cancel_downloads(self) -> None:
        """Performs cleanup for logic object.
        """
        for process in self.process_queue.queue:
            process.terminate()

    def _handle_process(self, process: subprocess.Popen) -> None:
        """Handle process flow and return when process has terminated.

        Args:
            process (subprocess.Popen): The process

        Raises:
            ConnectionError: If there was an error during authentication
        """
        assert process.stdout is not None
        assert process.stdin is not None

        responses = [
            (r"STEAM GUARD! Please enter .*: ", ProcessState.AUTH_TWO_FACTOR),
            (r"STEAM GUARD! Use .*\.\.\.", ProcessState.AUTH_STEAM_GUARD),
            (r"Enter account password.*: ", ProcessState.AUTH_PASSWORD_REQUIRED),
            (r"result: OK", ProcessState.AUTH_SUCCESS),
            (r"Error: InitializeSteam failed", ProcessState.AUTH_FAILED),
            (r"Authentication failed", ProcessState.AUTH_FAILED)
        ]

        while True:
            state = process.poll()
            # Process finished
            if state is not None:
                # Without error
                if state == 0:
                    return

                # With error
                raise ConnectionError("Download failed")

            line = process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue

            # Print output in real-time
            sys.stdout.write(line)
            sys.stdout.flush()

            # Check patterns
            response = ProcessState.UNKNOWN
            for (pattern, state) in responses:
                if re.search(pattern, line):
                    response = state
                    break

            match response:
                case ProcessState.AUTH_SUCCESS:
                    pass
                case ProcessState.AUTH_FAILED:
                    raise ConnectionError("Could not login to steam account")
                case ProcessState.AUTH_PASSWORD_REQUIRED | ProcessState.AUTH_STEAM_GUARD | ProcessState.AUTH_TWO_FACTOR:
                    self._handle_authentication(process, response)
                case ProcessState.FINISHED:
                    return
                case _:
                    pass

    def _handle_authentication(self, process: subprocess.Popen, state: ProcessState) -> None:
        """Handle interactive authentication flow.

        Args:
            process (subprocess.Popen): The process

        Raises:
            ConnectionError: If there was an error during authentication
        """
        def handle_password_required():
            assert process.stdout is not None
            assert process.stdin is not None

            password = self._open_temp_prompt("Code", "Please enter your password", True)

            if password is None:
                raise ConnectionError("Invalid password")

            process.stdin.write(password + '\n')
            process.stdin.flush()

        def handle_steam_guard():
            pass

        def handle_two_factor():
            assert process.stdout is not None
            assert process.stdin is not None

            code = self._open_temp_prompt("Code", "Please enter your 2FA login code", False)

            if code is None:
                raise ConnectionError("Invalid authentication code")

            process.stdin.write(code.upper() + '\n')
            process.stdin.flush()

        match state:
            case ProcessState.AUTH_PASSWORD_REQUIRED:
                handle_password_required()
            case ProcessState.AUTH_STEAM_GUARD:
                handle_steam_guard()
            case ProcessState.AUTH_TWO_FACTOR:
                handle_two_factor()
            case _:
                sys.stdout.write(f"Unexpected authentication state: {state}")

    def _open_temp_prompt(self, title: str, prompt: str, is_hidden: bool) -> str | None:
        """Opens a prompt widget with the requested title and prompt to enter information.

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
