from pathlib import Path

import vdf


def parse(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return vdf.load(f)


def find_has_run_keys(install_script: dict) -> list[tuple[str, str]]:
    """Recursively finds all has run registry keys for a given install script.

    Args:
        install_script (dict): The install script as parsed dictionary

    Returns:
        list[tuple[str, str]]: A list of (value_name, registry_path) registry keys from the install script
    """
    result = []

    def walk(node: dict | list, parent_key: str | None = None):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "HasRunKey" and isinstance(value, str):
                    if parent_key is not None:
                        result.append((parent_key, value))

                elif isinstance(value, (dict, list)):
                    walk(value, key)

        elif isinstance(node, list):
            for item in node:
                walk(item, parent_key)

    walk(install_script)

    return result
