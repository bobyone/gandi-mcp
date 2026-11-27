# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the work directory on the local file system."""

import os
import stat
from pathlib import Path

import pytest

from gandi_mcp.files.exceptions import (
    FileExistsInWorkDirectoryError,
    FileTooLargeError,
    OutsideWorkDirectoryError,
    UnreadableWorkFileError,
    WorkDirectoryError,
    WorkFileNotFoundError,
)
from gandi_mcp.files.local.local_work_directory import LocalWorkDirectory

ZONE = "@ 10800 IN A 192.0.2.1\r\nwww 10800 IN CNAME @\n"


@pytest.fixture
def directory(tmp_path: Path) -> LocalWorkDirectory:
    return LocalWorkDirectory(tmp_path / "work")


def test_writes_a_file_in_a_created_subdirectory(
    tmp_path: Path, directory: LocalWorkDirectory
) -> None:
    written = directory.write("zones\\example.com.zone", ZONE)

    target = tmp_path / "work" / "zones" / "example.com.zone"
    assert target.read_bytes() == ZONE.encode("utf-8")
    assert written.relative_path == "zones/example.com.zone"
    assert written.size == len(ZONE.encode("utf-8"))
    assert Path(written.absolute_path) == target.resolve()


def test_an_existing_file_is_kept_unless_overwriting_is_asked(
    directory: LocalWorkDirectory,
) -> None:
    directory.write("zone.txt", "first")

    with pytest.raises(FileExistsInWorkDirectoryError):
        directory.check_target("zone.txt")
    with pytest.raises(FileExistsInWorkDirectoryError):
        directory.write("zone.txt", "second")
    directory.write("zone.txt", "third", overwrite=True)

    assert directory.read("zone.txt", 100) == "third"


def test_a_directory_is_never_overwritten(tmp_path: Path, directory: LocalWorkDirectory) -> None:
    (tmp_path / "work" / "zones").mkdir(parents=True)

    with pytest.raises(FileExistsInWorkDirectoryError):
        directory.write("zones", "x", overwrite=True)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "   ",
        ".",
        "../outside.zone",
        "zones/../../outside.zone",
        "..\\outside.zone",
        "/etc/passwd",
        "\\\\server\\share\\x",
        "C:\\Windows\\x.zone",
        "C:x.zone",
        "zone.txt:stream",
        "zone\x00.txt",
        "bad|name",
        "zones /x",
        "x" * 256,
    ],
)
def test_paths_leading_out_or_not_allowed_are_refused(
    tmp_path: Path, directory: LocalWorkDirectory, path: str
) -> None:
    with pytest.raises(OutsideWorkDirectoryError):
        directory.write(path, "x")

    assert not (tmp_path / "outside.zone").exists()


def test_a_symbolic_link_leading_out_is_refused(
    tmp_path: Path, directory: LocalWorkDirectory
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "work").mkdir()
    try:
        (tmp_path / "work" / "escape").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links are not allowed for this user")

    with pytest.raises(OutsideWorkDirectoryError):
        directory.write("escape/x.zone", "x")
    with pytest.raises(OutsideWorkDirectoryError):
        directory.read("escape/x.zone", 100)

    assert not list(outside.iterdir())


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions")
def test_a_private_file_is_readable_by_its_owner_only(
    tmp_path: Path, directory: LocalWorkDirectory
) -> None:
    directory.write("tsig/bind.conf", "secret", private=True)

    mode = stat.S_IMODE((tmp_path / "work" / "tsig" / "bind.conf").stat().st_mode)
    assert mode == 0o600


def test_reads_a_utf8_file(tmp_path: Path, directory: LocalWorkDirectory) -> None:
    directory.write("zone.txt", "bücher 300 IN A 192.0.2.1\n")

    assert directory.read("zone.txt", 1000) == "bücher 300 IN A 192.0.2.1\n"


def test_reading_refuses_missing_large_and_binary_files(
    tmp_path: Path, directory: LocalWorkDirectory
) -> None:
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "big.zone").write_bytes(b"x" * 11)
    (tmp_path / "work" / "binary.zone").write_bytes(b"\xff\xfe\x00")

    with pytest.raises(WorkFileNotFoundError):
        directory.read("missing.zone", 10)
    with pytest.raises(FileTooLargeError):
        directory.read("big.zone", 10)
    with pytest.raises(UnreadableWorkFileError):
        directory.read("binary.zone", 10)


def test_a_write_failure_is_explained(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("not a directory", encoding="utf-8")
    directory = LocalWorkDirectory(blocker)

    with pytest.raises(WorkDirectoryError):
        directory.write("zone.txt", "x")
