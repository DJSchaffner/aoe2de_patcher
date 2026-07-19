import json
import argparse
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patches-file", default="remote/patches.json")
    parser.add_argument("--depots", required=True, help="JSON list of {depot_id, manifest_id}")
    parser.add_argument("--game-version", type=int, required=True)
    args = parser.parse_args()

    depots = json.loads(args.depots)
    patches_path = Path(args.patches_file)

    if patches_path.exists():
        with open(patches_path) as f:
            data = json.load(f)
    else:
        data = {"patches": []}

    last_version = data["patches"][-1].get("version") if data["patches"] else None
    if last_version == args.game_version:
        print("Game version unchanged, skipping write.")
        return

    data["patches"].append({
        "version": args.game_version,
        "date": int(time.time()),
        "depots": depots,
    })

    patches_path.parent.mkdir(parents=True, exist_ok=True)
    with open(patches_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Wrote new patch: game_version={args.game_version}")


if __name__ == '__main__':
    main()
