"""Update the shared PyData documentation version switcher during publication."""

import argparse
import json
import re
import shutil
from pathlib import Path

BASE_URL = "https://datasophos.github.io/NexusLIMS-CDCS"
VERSION = re.compile(r"^v(\d+)\.(\d+)\.(\d+)-nx(\d+)$")


def build_entries(pages):
    """List deployed versions, using the stable deployment's recorded version."""
    entries = []
    if (pages / "latest").is_dir():
        entries.append({"name": "Latest development", "version": "dev", "url": f"{BASE_URL}/latest/"})
    marker = pages / "stable" / "version.txt"
    stable = marker.read_text().strip() if marker.is_file() else None
    if stable and VERSION.fullmatch(stable):
        entries.append({"name": f"{stable} (stable)", "version": stable, "url": f"{BASE_URL}/stable/", "preferred": True})
    releases = []
    for path in pages.iterdir():
        match = VERSION.fullmatch(path.name)
        if path.is_dir() and match and path.name != stable:
            releases.append((tuple(map(int, match.groups())), path.name))
    for _, name in sorted(releases, reverse=True):
        entries.append({"name": name, "version": name, "url": f"{BASE_URL}/{name}/"})
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", type=Path)
    parser.add_argument("site", type=Path)
    parser.add_argument("destination")
    parser.add_argument("--stable", action="store_true")
    args = parser.parse_args()
    if args.destination != "latest" and not VERSION.fullmatch(args.destination):
        parser.error("destination must be latest or a CDCS release tag")
    if args.stable and args.destination == "latest":
        parser.error("stable requires a release tag")
    targets = [args.destination] + (["stable"] if args.stable else [])
    for target in targets:
        dest = args.pages / target
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(args.site, dest)
        if target == "stable":
            (dest / "version.txt").write_text(args.destination + "\n")
    (args.pages / "switcher.json").write_text(json.dumps(build_entries(args.pages), indent=2) + "\n")
    (args.pages / "index.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta http-equiv="refresh" content="0; url=stable/">\n'
        '<title>NexusLIMS-CDCS documentation</title>\n'
        '</head>\n<body>\n'
        '<p>Redirecting to the <a href="stable/">stable documentation</a>.</p>\n'
        '</body>\n</html>\n'
    )


if __name__ == "__main__":
    main()
