import argparse
import subprocess
import os

from pathlib import Path

from src.utils import get_exe_name, get_game_version


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--app-id", type=int, required=True)
    p.add_argument("--depot-id", type=int, required=True)
    p.add_argument("--manifest-id", required=True)
    p.add_argument("--download-dir", default="./exe_download")
    p.add_argument("--depotdownloader", default="./depotdownloader/DepotDownloader")
    args = p.parse_args()

    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    filelist = Path(download_dir) / "filelist.txt"
    filelist.write_text(get_exe_name() + "\n")

    subprocess.run([
        args.depotdownloader,
        "-app", str(args.app_id),
        "-depot", str(args.depot_id),
        "-manifest", args.manifest_id,
        "-filelist", str(filelist),
        "-dir", args.download_dir,
        "-username", os.environ["STEAM_USERNAME"],
        "-password", os.environ["STEAM_PASSWORD"],
        "-remember-password",
    ], check=True)

    version = get_game_version(Path(args.download_dir))
    print(version)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"game_version={version}\n")


if __name__ == '__main__':
    main()
