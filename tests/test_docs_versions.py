"""Check the published documentation version index."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "docs_versions", Path(__file__).resolve().parents[1] / "scripts/docs_versions.py"
)
versions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versions)


def test_version_index_uses_deployed_directories_and_stable_marker(tmp_path):
    for name in ("latest", "stable", "v3.23.0-nx2", "v3.23.0-nx10", "v3.21.0-nx1", "unrelated"):
        (tmp_path / name).mkdir()
    (tmp_path / "stable" / "version.txt").write_text("v3.23.0-nx2\n")
    entries = versions.build_entries(tmp_path)
    assert [entry["version"] for entry in entries] == [
        "dev", "v3.23.0-nx2", "v3.23.0-nx10", "v3.21.0-nx1"
    ]
    assert entries[1]["preferred"] is True
    assert entries[1]["url"].endswith("/stable/")


def test_first_deployment_does_not_link_missing_stable(tmp_path):
    (tmp_path / "latest").mkdir()
    assert [entry["version"] for entry in versions.build_entries(tmp_path)] == ["dev"]


def test_publishing_release_replaces_stable_and_preserves_older_versions(tmp_path):
    pages = tmp_path / "pages"
    site = tmp_path / "site"
    pages.mkdir()
    site.mkdir()
    (site / "index.html").write_text("new release")
    old = pages / "v3.21.0-nx1"
    old.mkdir()
    (old / "index.html").write_text("older release")
    stable = pages / "stable"
    stable.mkdir()
    (stable / "obsolete.html").write_text("old")
    subprocess.run(
        [sys.executable, str(spec.origin), str(pages), str(site), "v3.23.0-nx0", "--stable"],
        check=True,
    )
    assert (stable / "version.txt").read_text().strip() == "v3.23.0-nx0"
    assert not (stable / "obsolete.html").exists()
    assert (old / "index.html").read_text() == "older release"
    entries = json.loads((pages / "switcher.json").read_text())
    assert [entry["version"] for entry in entries] == ["v3.23.0-nx0", "v3.21.0-nx1"]
