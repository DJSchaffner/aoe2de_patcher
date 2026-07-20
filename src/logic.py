import os
import pathlib
import shutil
import tempfile

from depot_downloader_helper import DepotDownloaderHelper
from web_helper import WebHelper
import manifest
import utils


class Logic:
    APP_ID = 813780

    def __init__(self):
        self.webhook = WebHelper()
        # The earliest patch that works was released after direct x update
        # @TODO Try to figure out a way to patch to earlier patches than this: time.struct_time((2020, 2, 17, 0, 0, 0, 0, 48, 0))
        self.download_dir = utils.base_path() / "download"
        self.manifest_dir = utils.base_path() / "manifests"
        self.backup_dir = utils.base_path() / "backup"
        self.patch_list = self.webhook.query_patches()
        self.depot_downloader_helper = DepotDownloaderHelper()

    def patch(self, username: str, target_version: int) -> None:
        """Start patching the game with the downloaded files.

        Args:
            username (str): The username
            target_version (int): The version to patch to
        """
        try:
            # Check some stuff
            if not hasattr(self, "game_dir") or self.game_dir is None:
                raise Exception("Please select a game directory")

            if username == "":
                raise Exception("Please enter a username")

            installed_version = utils.get_game_version(self.game_dir)
            if installed_version == target_version:
                raise Exception("The selected version is already installed")

            print("Starting download phase...")

            self._download_patch(username, installed_version, target_version)

            print("Finished downloading files")

            print("Starting backup...")

            self._backup()

            print("Finished backup")

            print("Patching files...")

            self._move_patch()

            print("Finished patching files")
        except Exception:
            raise

    def restore(self) -> None:
        """Restores the game directory using the backed up files and downloaded files.
        """
        # Check some stuff
        if not hasattr(self, "game_dir") or self.game_dir is None:
            raise Exception("Please select a game directory")

        if not self.backup_dir.exists():
            raise Exception("Backup directory doesn't exist")

        if len(os.listdir(self.backup_dir.absolute())) == 0:
            raise Exception("No backup stored")

        # Remove added files from the path
        try:
            print("Removing patched files...")
            utils.remove_patched_files(self.game_dir, self.download_dir, True)
            print("Finished removing patched files")

            # Copy backed up files to game path again
            try:
                print("Restoring backup...")
                shutil.copytree(self.backup_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok=True)
                print("Finished restoring backup")
            except Exception:
                raise Exception("Error restoring files!")
        except Exception:
            raise Exception("Error removing files!")

    def set_game_dir(self, dir: pathlib.Path) -> None:
        """Tries to set the game directory, if successful return True. Otherwise return False.

        Args:
            dir (pathlib.Path): The directory to be set
        """
        aoe_binary = dir / "AoE2DE_s.exe"

        if not aoe_binary.exists():
            raise Exception("Invalid game directory")

        self.game_dir = dir

        print(f"Game directory set to: {dir.absolute()}")
        print(f"Installed version detected: {utils.get_game_version(self.game_dir)}")

    def get_patch_list(self) -> list[dict]:
        """Returns the patch list.

        Returns:
            list: The list of documented patches
        """
        return self.patch_list

    def cancel_downloads(self) -> None:
        """Performs cleanup for logic object.
        """
        self.depot_downloader_helper.cancel_downloads()

    def _download_patch(self, username: str, installed_version: int, target_version: int) -> None:
        """Download the given patch using the steam account username.

        Args:
            username (str): The username
            installed_version (int): The currently installed version
            target_version (int): The target version
        """
        # dotnet is required to proceed
        if not (utils.check_dotnet()):
            raise Exception("DOTNET Core required but not found!")

        update_list = []
        tmp_files = []

        # Remove previous download folder if it exists
        # Create empty folders afterwards
        if self.download_dir.exists():
            try:
                shutil.rmtree(self.download_dir.absolute())
            except Exception:
                raise Exception("Error removing previous download directory")

        self.download_dir.mkdir()

        # Remove previous manifests folder if it exists
        # Create empty folders afterwards
        if self.manifest_dir.exists():
            try:
                shutil.rmtree(self.manifest_dir.absolute())
            except Exception:
                raise Exception("Error removing previous manifest directory")

        self.manifest_dir.mkdir()

        print("Generating list of changes")

        # Filter list of patches for current and target version
        filtered_patches = list(filter(lambda x: x["version"] == installed_version or x["version"] == target_version, self.patch_list))

        # One of the two patches is not in the list of patches. Most likely the installed version, cannot patch
        if len(filtered_patches) != 2:
            raise Exception("The installed version currently doesn't support downgrading. Please be patient or notify me on GitHub!")

        # Store current and target patch
        current_patch = list(filter(lambda x: x["version"] == installed_version, self.patch_list))[0]
        target_patch = list(filter(lambda x: x["version"] == target_version, filtered_patches))[0]

        # Only support patching via filelists to an older version atm
        if installed_version < target_version:
            raise Exception("Patching forward is currently unavailable. Please use Steam to get to the latest version and then patch backwards")

        # Iterate depots of current and target patch together
        for current_depot, target_depot in zip(current_patch["depots"], target_patch["depots"]):
            # Check if depot id changes (VCRedist for example does change sometimes)
            # (Temporary?) solution just skip non-matching depot since old depots are no longer available and hope it still works
            if current_depot["depot_id"] == target_depot["depot_id"]:
                depot_id = current_depot["depot_id"]
                current_manifest_id = current_depot["manifest_id"]
                target_manifest_id = target_depot["manifest_id"]

                changes = self._get_filelist(username, depot_id, current_manifest_id, target_manifest_id)

                # Files have changed, store changes to temp file and add to update list
                if changes is not None:
                    # Create temp file
                    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)

                    # Store file name for deletion later on
                    tmp_files.append(tmp.name)

                    # Write content to file
                    tmp.write("\n".join(changes))
                    tmp.close()

                    # Add update element to list
                    update_list.append({'depot_id': depot_id, 'manifest_id': target_manifest_id, 'filelist': tmp.name})
            else:
                print(f"Depot ID not matching, discarding pair ({current_depot['depot_id']}, {target_depot['depot_id']})")

        print("Downloading files")

        # Loop all necessary updates
        for element in update_list:
            # Stop if a download didn't succeed
            self._download_depot(username, element['depot_id'], element['manifest_id'], element['filelist'])

        # Remove created temp files
        for tmp in tmp_files:
            os.unlink(tmp)

    def _move_patch(self) -> None:
        """Move downloaded patch files to game directory.
        """
        try:
            shutil.copytree(self.download_dir.absolute(), self.game_dir.absolute(), dirs_exist_ok=True)
        except Exception:
            raise

    def _backup(self) -> None:
        """Backup game folder and in current directory.
        """
        try:
            # Remove previous backup folder if it exists
            # Create empty folders afterwards
            if self.backup_dir.exists():
                try:
                    shutil.rmtree(self.backup_dir.absolute())
                except Exception:
                    raise Exception("Error removing previous backup directory")
            self.backup_dir.mkdir()

            utils.backup_files(self.game_dir, self.download_dir, self.backup_dir, True)
        except Exception:
            raise

    def _download_manifest(self, username: str, depot_id: int, manifest_id: int) -> None:
        """Download a specific manifest from the given depot using the given credentials.

        Args:
            username (str): The username
            depot_id (int): The selected depot
            manifest_id (int): The manifest id for the depot

        Raises:
            ConnectionError: If there was an error during authentication
        """
        args = ["-app", str(self.APP_ID),
                "-depot", str(depot_id),
                "-manifest", str(manifest_id),
                "-username", username,
                "-remember-password",
                "-dir", str(self.manifest_dir),
                "-manifest-only"]

        self.depot_downloader_helper.execute(args)

    def _download_depot(self, username: str, depot_id: int, manifest_id: int, filelist: str) -> None:
        """Download a specific depot using the manifest id from steam using the given credentials.

        Args:
            username (str): The username
            depot_id (int): The selected depot
            manifest_id (int): The manifest id for the depot
            filelist (str): The name of the file used as filelist

        Raises:
            ConnectionError: If there was an error during authentication
        """
        args = ["-app", str(self.APP_ID),
                "-depot", str(depot_id),
                "-manifest", str(manifest_id),
                "-username", username,
                "-remember-password",
                "-dir", str(self.download_dir),
                "-filelist", filelist]

        self.depot_downloader_helper.execute(args)

    def _get_filelist(self, username: str, depot_id: int, current_manifest_id: int, target_manifest_id: int) -> list[str] | None:
        """Get a list of all files that have been removed or modified between the current and target version.

        Args:
            username (str): The username
            depot_id (int): The selected depot
            current_manifest_id (int): The current manifest id for the depot
            target_manifest_id (id): The target manifest id for the depot

        Returns:
            list: A list of changed filenames
        """
        # Only need to check for changes if manifest changed
        if current_manifest_id == target_manifest_id:
            return None

        removed = []
        modified = []

        # Download manifests
        self._download_manifest(username, depot_id, current_manifest_id)
        self._download_manifest(username, depot_id, target_manifest_id)

        # Read manifest files
        current_manifest = manifest.read_manifest(self.manifest_dir / f"manifest_{depot_id}_{current_manifest_id}.txt")
        target_manifest = manifest.read_manifest(self.manifest_dir / f"manifest_{depot_id}_{target_manifest_id}.txt")

        # Initialize file sets
        current_set = set(current_manifest.files)
        target_set = set(target_manifest.files)

        # Find all removed files (Result contains removed files and files with different hash)
        diff_removed = list(target_set.difference(current_set))
        diff_removed_names = set([x[0] for x in diff_removed])

        # Find all added files (Result contains added files and files with different hash)
        diff_added = list(current_set.difference(target_set))
        diff_added_names = set([x[0] for x in diff_added])

        # Find all removed files (Remove files with same name but different hash)
        removed = set.difference(diff_removed_names, diff_added_names)

        # Find all modified files (Retain files with same name but different hash)
        modified = set.intersection(diff_removed_names, diff_added_names)

        changes = []

        changes += removed
        changes += modified

        return changes

    def _get_filelist_current(self, username: str, password: str, depot_id: int, manifest_id: int) -> list[str]:
        """Get a list of all files current files of a depot.

        Args:
            username (str): The username
            depot_id (int): The selected depot
            manifest_id (int): The current manifest id for the depot

        Returns:
            list: A list of current file names for the depot
        """
        # Download manifests
        self._download_manifest(username, depot_id, manifest_id)

        # Read manifest files
        current_manifest = manifest.read_manifest(self.manifest_dir / f"manifest_{depot_id}_{manifest_id}.txt")

        return current_manifest.files
