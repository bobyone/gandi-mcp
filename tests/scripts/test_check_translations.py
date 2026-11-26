# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the translation checker, on synthetic catalogs and on the real ones."""

import logging
from collections.abc import Mapping
from pathlib import Path

import pytest
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po

from scripts import check_translations as checker

SOURCE = 'from gettext import gettext as _\n_("Hello {name}")\n'


def write_catalog(path: Path, entries: Mapping[str, str | tuple[str, ...]], **flags: str) -> None:
    catalog = Catalog(locale=None if path.suffix == ".pot" else "fr")
    for identifier, string in entries.items():
        catalog.add(identifier, string, flags=[flags[identifier]] if identifier in flags else [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        write_po(stream, catalog)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text(SOURCE, encoding="utf-8")
    write_catalog(tmp_path / "locales" / "messages.pot", {"Hello {name}": ""})
    return tmp_path


def run(project: Path) -> int:
    return checker.main(["--locales", str(project / "locales"), "--source", str(project / "src")])


def fr_catalog(project: Path) -> Path:
    return project / "locales" / "fr" / "LC_MESSAGES" / "messages.po"


def test_valid_catalogs_pass_and_count_reviews(
    project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    write_catalog(
        fr_catalog(project),
        {"Hello {name}": "Bonjour {name}"},
        **{"Hello {name}": checker.NEEDS_REVIEW},
    )

    with caplog.at_level(logging.INFO):
        assert run(project) == 0
    assert "1 translations awaiting native review" in caplog.text


@pytest.mark.parametrize(
    ("entries", "error"),
    [
        ({}, "missing key"),
        ({"Hello {name}": ""}, "empty translation"),
        ({"Hello {name}": "Bonjour {nom}"}, "parameters differ"),
        ({"Hello {name}": "Bonjour {name}", "Bye": "Salut"}, "unused key"),
    ],
)
def test_catalog_errors(
    project: Path, caplog: pytest.LogCaptureFixture, entries: dict[str, str], error: str
) -> None:
    write_catalog(fr_catalog(project), entries)

    assert run(project) == 1
    assert error in caplog.text


def test_outdated_template_fails(project: Path, caplog: pytest.LogCaptureFixture) -> None:
    write_catalog(project / "locales" / "messages.pot", {"Removed": ""})
    write_catalog(fr_catalog(project), {"Removed": "Retiré"})

    assert run(project) == 1
    assert "lacks a key used in the code" in caplog.text
    assert "unused key" in caplog.text


def test_obsolete_entries_fail(project: Path, caplog: pytest.LogCaptureFixture) -> None:
    path = fr_catalog(project)
    write_catalog(path, {"Hello {name}": "Bonjour {name}"})
    with path.open("a", encoding="utf-8") as stream:
        stream.write('\n#~ msgid "Old"\n#~ msgstr "Vieux"\n')

    assert run(project) == 1
    assert "obsolete key" in caplog.text


def test_missing_catalogs_fail(project: Path, caplog: pytest.LogCaptureFixture) -> None:
    assert run(project) == 1
    assert "no catalog found" in caplog.text


def test_plural_placeholders() -> None:
    assert checker.placeholders(("{count} domain", "{count} domains", "{{literal}}")) == {"count"}


def test_repository_catalogs_are_consistent() -> None:
    assert checker.main([]) == 0
