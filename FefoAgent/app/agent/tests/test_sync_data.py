"""Smoke tests for scripts/sync_data.sh (always uses temp source and destination)."""

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts" / "sync_data.sh"
SUBDIRS = ("raw", "config", "policy")


def run_sync(dest: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "SYNC_DATA_DEST": str(dest)}
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    """Relative path -> content for every file; independent of mtime."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@pytest.fixture
def source(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    for sub in (*SUBDIRS, "scenarios"):
        (src / sub).mkdir(parents=True)
        (src / sub / f"{sub}.csv").write_text(f"{sub},data\nşğıİçöü₺,1\n", encoding="utf-8")
    (src / "raw" / "nested").mkdir()
    (src / "raw" / "nested" / "deep.csv").write_text("a,b\n", encoding="utf-8")
    return src


@pytest.fixture
def dest(tmp_path: Path) -> Path:
    return tmp_path / "dest"


def test_copies_three_dirs_and_not_scenarios(source: Path, dest: Path):
    result = run_sync(dest, "--from", str(source))
    assert result.returncode == 0, result.stderr
    for sub in SUBDIRS:
        assert (dest / sub / f"{sub}.csv").read_bytes() == (source / sub / f"{sub}.csv").read_bytes()
    assert (dest / "raw" / "nested" / "deep.csv").is_file()
    assert not (dest / "scenarios").exists()
    assert not list(dest.rglob("scenarios.csv"))
    assert str(source) in result.stdout and str(dest) in result.stdout


def test_source_is_unchanged(source: Path, dest: Path):
    before = snapshot(source)
    dirs_before = sorted(str(p.relative_to(source)) for p in source.rglob("*") if p.is_dir())
    assert run_sync(dest, "--from", str(source)).returncode == 0
    assert snapshot(source) == before
    assert sorted(str(p.relative_to(source)) for p in source.rglob("*") if p.is_dir()) == dirs_before


def test_stale_destination_files_are_replaced(source: Path, dest: Path):
    for sub in SUBDIRS:
        (dest / sub).mkdir(parents=True)
        (dest / sub / "stale.csv").write_text("old")
        (dest / sub / f"{sub}.csv").write_text("outdated")
    assert run_sync(dest, "--from", str(source)).returncode == 0
    for sub in SUBDIRS:
        assert not (dest / sub / "stale.csv").exists()
        assert (dest / sub / f"{sub}.csv").read_bytes() == (source / sub / f"{sub}.csv").read_bytes()


def test_missing_source_warns_and_leaves_destination_untouched(tmp_path: Path, dest: Path):
    (dest / "raw").mkdir(parents=True)
    (dest / "raw" / "keep.csv").write_text("keep")
    before = snapshot(dest)
    missing = tmp_path / "does-not-exist"
    result = run_sync(dest, "--from", str(missing))
    assert "warning" in result.stderr.lower()
    assert str(missing) in result.stderr
    assert snapshot(dest) == before


def test_missing_source_subdir_warns_and_leaves_that_dir_untouched(source: Path, dest: Path):
    (dest / "policy").mkdir(parents=True)
    (dest / "policy" / "keep.csv").write_text("keep")
    (source / "policy" / "policy.csv").unlink()
    (source / "policy").rmdir()
    result = run_sync(dest, "--from", str(source))
    assert "warning" in result.stderr.lower()
    assert "policy" in result.stderr
    assert (dest / "policy" / "keep.csv").read_text() == "keep"
    assert (dest / "raw" / "raw.csv").is_file()


def test_from_without_value_exits_nonzero_with_usage(dest: Path):
    result = run_sync(dest, "--from")
    assert result.returncode != 0
    assert "Usage" in result.stderr
    assert not dest.exists()


def test_unknown_option_exits_nonzero_with_usage(dest: Path):
    result = run_sync(dest, "--bogus")
    assert result.returncode != 0
    assert "Usage" in result.stderr
    assert not dest.exists()
