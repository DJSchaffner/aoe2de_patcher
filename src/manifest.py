from dataclasses import dataclass
import pathlib
import re
from typing import Any


@dataclass
class Manifest():
    depot: int
    id: int
    date: Any
    num_files: int
    num_chunks: int
    size_disk: int
    size_compressed: int
    files: list[str]


def read_manifest(file: pathlib.Path) -> Manifest:
    """Parse a given manifest file and return a manifest object.

    Args:
        file (pathlib.Path): Path to the manifest file

    Returns:
        Manifest: The parsed manifest object
    """
    def expectMatch(pattern: str, line: str) -> re.Match[str]:
        match = re.match(pattern, line)

        if match is None:
            raise ValueError(f"Could not match pattern '{pattern}' against line '{line}'")

        return match

    with open(file, "r") as f:
        depot = 0
        id = 0
        date = 0
        num_files = 0
        num_chunks = 0
        size_disk = 0
        size_compressed = 0
        files = []

        try:
            # First line contains depot id
            line = f.readline()
            depot = int(expectMatch(r".* (\d+)", line).groups()[0])

            # Second lines is empty
            # Third contains manifest id and date
            line = f.readline()
            line = f.readline()
            groups = expectMatch(r".* : (\d+) \/ (.+)", line).groups()
            id = int(groups[0])
            date = str(groups[1])    # (Temporary) workaround since date isn't used anyways.
            # Date format seems to be localized... @TODO find a way to universally parse date string
            # date = time.mktime(time.strptime(groups[1], "%d.%m.%Y %H:%M:%S"))

            # Fourth line contains number of files
            line = f.readline()
            groups = expectMatch(r".* : (\d+)", line).groups()
            num_files = int(groups[0])

            # Fifth line contains number of chunks
            line = f.readline()
            groups = expectMatch(r".* : (\d+)", line).groups()
            num_chunks = int(groups[0])

            # Sixth line contains size on disk
            line = f.readline()
            groups = expectMatch(r".* : (\d+)", line).groups()
            size_disk = int(groups[0])

            # Seventh line contains size compressed
            line = f.readline()
            groups = expectMatch(r".* : (\d+)", line).groups()
            size_compressed = int(groups[0])

            # Eighth line is empty
            # Ninth line is empty
            # Tenth line contains headers
            # Eleventh line until EOF contains one file per line
            line = f.readline()
            line = f.readline()
            line = f.readline()
            while line := f.readline():
                # Extract file hash and name
                match = expectMatch(r"\s+\d+\s+\d+\s+(?P<hash>.{40})\s+\d+\s+(?P<name>.+)", line)
                files.append((match.group("name"), match.group("hash")))

            return Manifest(depot, id, date, num_files, num_chunks, size_disk, size_compressed, files)
        except ValueError:
            raise
