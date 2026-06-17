import signal
import sys
from queue import Queue

import pexpect
import pexpect.popen_spawn
import tkinter
import tkinter.simpledialog

import utils


class DepotDownloaderHelper:
    def __init__(self):
        self.process_queue = Queue()

    def execute(self, options: list, password: str):
        """Execute the DepotDownloader with the given options as arguments. Return True if successful.

        Args:
            options (list): A list of options that will be passed to DepotDownloader directly

        Raises:
            ConnectionError: If there was an error during authentication
        """
        args = ["dotnet", str(utils.resource_path('DepotDownloader/DepotDownloader.dll').absolute())] + options

        # Spawn process and store in queue
        p = pexpect.popen_spawn.PopenSpawn(args, encoding="utf-8")
        self.process_queue.put(p)
        p.logfile_read = sys.stdout

        try:
            self._handle_authentication(password, p)

            # Wait for program to finish
            p.expect(pexpect.EOF, timeout=None)
        except pexpect.exceptions.TIMEOUT:
            raise BaseException("Error waiting for DepotDownloader to start")
        except ConnectionError:
            raise
        finally:
            # Remove process from queue after working with it
            self.process_queue.get()

    def cancel_downloads(self):
        """Performs cleanup for logic object.
        """
        for process in self.process_queue.queue:
            process.kill(signal.SIGTERM)

    def _handle_authentication(self, password: str, p: pexpect.popen_spawn.PopenSpawn):
        """Handle interactive authentication flow

        Args:
            password (str): Password

        Raises:
            ConnectionError: If there was an error during authentication
        """
        responses = [
            pexpect.EOF,
            "STEAM GUARD! Please enter .*: ",
            "STEAM GUARD! Use .*\\.\\.\\.",
            "Enter account password.*: ",
            "result: OK"
        ]

        # Default timeout in seconds
        timeout = 30
        response = p.expect(responses, timeout=timeout)

        # Error
        if response == 0:
            raise ConnectionError("Error logging into account")

        # Code required
        elif response == 1:
            # Open popup for 2FA Code
            # Create temporary parent window to prevent error with visibility
            # @TODO add timer as actual timer or bar running out
            temp = tkinter.Tk()
            temp.withdraw()
            code = tkinter.simpledialog.askstring(title="Code", prompt="Please enter your 2FA login code", parent=temp)
            temp.destroy()

            # Cancel was clicked
            if code is None:
                raise ConnectionError("Invalid authentication code")
            # Code was entered
            else:
                # Send 2fa code to child process and check the result
                p.sendline(code.upper())

                # Invalid code
                if p.expect(responses, timeout=timeout) == 1:
                    raise ConnectionError("Invalid authentication code")

        # Steam Guard
        elif response == 2:
            pass

        elif response == 3:
            p.sendline(password)
            self._handle_authentication(password, p)
