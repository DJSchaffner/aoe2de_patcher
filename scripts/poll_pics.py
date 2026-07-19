import json
import argparse
import os
import time
from pathlib import Path
from steam.client import SteamClient


APP_ID = 813780
DEPOT_IDS = [
    813781,
    813782,
    813783,
    813784,
    813786,
    813787
]


def load_patches(path: Path) -> dict:
    """Load the current content of the patches JSON or an empty one if it doesn't exist.

    Args:
        path (Path): The path to the patches file

    Returns:
        dict: A dictionary containing the currently documented patches
    """
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"patches": []}


def fetch_current_build() -> tuple[int, dict]:
    """Fetches the current build id and a list of depots with their current manifest ids.

    Raises:
        Exception: When app info could not be queried

    Returns:
        tuple[int, dict]: The current build id and a dictionary containing depot ids as key and their manifest id as value
    """
    client = SteamClient()
    client.anonymous_login()
    info = client.get_product_info(apps=[APP_ID])

    if info is None:
        raise Exception("Could not get current app info.")

    depots: dict = info['apps'][APP_ID]['depots']
    build_id = int(depots.get('branches', {}).get('public', {}).get('buildid'))

    result = {}
    for depot_id, depot in depots.items():
        if depot_id.isdigit() and isinstance(depot, dict) and 'manifests' in depot:
            gid = depot['manifests'].get('public', {}).get('gid')
            if gid:
                result[int(depot_id)] = int(gid)

    client.disconnect()

    return build_id, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='remote/patches.json')
    patches_path = Path(parser.parse_args().out)

    data = load_patches(patches_path)
    build_id, manifests = fetch_current_build()

    last_patch = data['patches'][-1] if data['patches'] else None
    last_depots = {}
    if last_patch:
        last_depots = {x['depot_id']: x['manifest_id'] for x in last_patch['depots']}

    changes = []
    new_depot_entries = []
    for depot_id in DEPOT_IDS:
        new_manifest = manifests.get(depot_id)
        if new_manifest is None:
            continue

        new_depot_entries.append({"depot_id": depot_id, "manifest_id": new_manifest})
        if last_depots.get(depot_id) != new_manifest:
            changes.append(f"depot {depot_id}: {last_depots.get(depot_id)} -> {new_manifest}")

    gh_output = os.environ.get('GITHUB_OUTPUT')

    if not changes:
        print("No changes detected.")

        # Write output for GitHub Actions
        if gh_output:
            with open(gh_output, 'a') as f:
                f.write("changed=false\n")

        return

    data['patches'].append({
        "version": build_id,
        "date": int(time.time()),
        "depots": new_depot_entries
    })

    patches_path.parent.mkdir(parents=True, exist_ok=True)
    with open(patches_path, 'w') as f:
        json.dump(data, f, indent=4)

    summary = "; ".join(changes)
    print(f"Changes detected: {summary}")

    # Write output for GitHub Actions
    if gh_output:
        with open(gh_output, 'a') as f:
            f.write("changed=true\n")
            f.write(f"version={build_id}\n")


if __name__ == '__main__':
    main()
