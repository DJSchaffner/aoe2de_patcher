import json
import argparse
import os
from pathlib import Path
from steam.client import SteamClient


def load_last_patch(path: Path) -> dict:
    """Load the content of the last patch from the patches JSON or an empty one if it doesn"t exist.

    Args:
        path (Path): The path to the patches file

    Returns:
        dict: A dictionary containing the currently documented patches
    """
    if not path.exists():
        return {}

    with open(path) as f:
        data = json.load(f)

    if not data.get("patches"):
        return {}

    return {d["depot_id"]: d["manifest_id"] for d in data["patches"][-1]["depots"]}


def fetch_current_build(app_id: int) -> tuple[int, dict]:
    """Fetches the current build id and a list of depots with their current manifest ids.

    Raises:
        Exception: When app info could not be queried

    Returns:
        tuple[int, dict]: The current build id and a dictionary containing depot ids as key and their manifest id as value
    """
    client = SteamClient()
    client.anonymous_login()
    info = client.get_product_info(apps=[app_id])

    if info is None:
        raise Exception("Could not get current app info.")

    depots: dict = info["apps"][app_id]["depots"]
    build_id = int(depots.get("branches", {}).get("public", {}).get("buildid"))

    result = {}
    for depot_id, depot in depots.items():
        if depot_id.isdigit() and isinstance(depot, dict) and "manifests" in depot:
            gid = depot["manifests"].get("public", {}).get("gid")
            if gid:
                result[int(depot_id)] = int(gid)

    client.disconnect()

    return build_id, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-id", type=int, required=True)
    parser.add_argument("--depots", nargs="+", type=int, required=True,
                        help="Depot IDs to track, e.g. --depots 813781 813782")
    parser.add_argument("--exe-depot-id", type=int, required=True)
    parser.add_argument("--out", default="remote/patches.json")
    args = parser.parse_args()

    app_id = args.app_id
    depot_ids = args.depots
    patches_path = Path(args.out)
    exe_depot_id = args.exe_depot_id

    last_patch_depots = load_last_patch(patches_path)
    _, manifests = fetch_current_build(app_id)

    exe_manifest = manifests.get(exe_depot_id)
    new_depot_entries = [
        {"depot_id": d, "manifest_id": m}
        for d, m in manifests.items() if d in depot_ids
    ]

    gh_output = os.environ.get("GITHUB_OUTPUT")

    is_changed = last_patch_depots.get(exe_depot_id) != exe_manifest
    if not is_changed:
        print("No changes detected.")

        # Write output for GitHub Actions
        if gh_output:
            with open(gh_output, "a") as f:
                f.write("changed=false\n")

        return

    print("Changes detected.")
    print(f"exe_manifest: {exe_manifest}")

    # Write output for GitHub Actions
    if gh_output:
        with open(gh_output, "a") as f:
            f.write("changed=true\n")
            f.write(f"exe_manifest={exe_manifest}\n")
            f.write(f"depots={json.dumps(new_depot_entries)}\n")


if __name__ == '__main__':
    main()
