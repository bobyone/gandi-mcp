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

SOURCE = (
    "from gettext import gettext as _, ngettext\n"
    '_("Hello {name}")\n'
    'ngettext("{count} domain", "{count} domains", 2)\n'
)
HELLO = "Hello {name}"
DOMAINS = ("{count} domain", "{count} domains")
VALID: dict[str | tuple[str, ...], str | tuple[str, ...]] = {
    HELLO: "Bonjour {name}",
    DOMAINS: ("{count} domaine", "{count} de domaines", "{count} domaines"),
}

Entries = Mapping[str | tuple[str, ...], str | tuple[str, ...]]


def write_catalog(path: Path, entries: Entries, review: frozenset[str] = frozenset()) -> None:
    catalog = Catalog(locale=None if path.suffix == ".pot" else "fr")
    for identifier, string in entries.items():
        key = identifier[0] if isinstance(identifier, tuple) else identifier
        catalog.add(identifier, string, flags=[checker.NEEDS_REVIEW] if key in review else [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        write_po(stream, catalog)


def declare(project: Path, *locales: str) -> None:
    listed = ", ".join(f'"{locale}"' for locale in locales)
    (project / "locales" / checker.LOCALES_FILE).write_text(
        f"supported = [{listed}]\n", encoding="utf-8"
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text(SOURCE, encoding="utf-8")
    write_catalog(tmp_path / "locales" / "messages.pot", {HELLO: "", DOMAINS: ("", "")})
    declare(tmp_path, "fr")
    return tmp_path


def run(project: Path) -> int:
    return checker.main(["--locales", str(project / "locales"), "--source", str(project / "src")])


def fr_catalog(project: Path) -> Path:
    return project / "locales" / "fr" / "LC_MESSAGES" / "messages.po"


def test_valid_catalogs_pass_and_count_reviews(
    project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    write_catalog(fr_catalog(project), VALID, review=frozenset({HELLO}))

    with caplog.at_level(logging.INFO):
        assert run(project) == 0
    assert "1 translations awaiting native review" in caplog.text


@pytest.mark.parametrize(
    ("entries", "error"),
    [
        ({DOMAINS: VALID[DOMAINS]}, "missing key"),
        ({**VALID, HELLO: ""}, "empty translation"),
        ({**VALID, HELLO: "Bonjour {nom}"}, "parameters differ"),
        ({**VALID, "Bye": "Salut"}, "unused key"),
        (
            {**VALID, DOMAINS: ("{count} domaine", "de domaines", "{count} domaines")},
            "in plural form 1",
        ),
        # A singular catalog entry for a plural source, with the right parameters.
        ({HELLO: VALID[HELLO], DOMAINS[0]: "{count} domaines"}, "plural shape differs"),
        (
            {
                ("Hello {name}", "Hello {name}s"): ("a {name}", "b {name}", "c {name}"),
                **{DOMAINS: VALID[DOMAINS]},
            },
            "plural shape differs (source is singular)",
        ),
        # Babel pads a missing plural form with an empty string when reading the catalog.
        ({**VALID, DOMAINS: ("{count} domaine", "{count} domaines")}, "empty translation"),
        (
            {HELLO: VALID[HELLO], ("{count} domain", "{count} names"): VALID[DOMAINS]},
            "plural source text differs",
        ),
    ],
)
def test_catalog_errors(
    project: Path, caplog: pytest.LogCaptureFixture, entries: Entries, error: str
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
    write_catalog(path, VALID)
    with path.open("a", encoding="utf-8") as stream:
        stream.write('\n#~ msgid "Old"\n#~ msgstr "Vieux"\n')

    assert run(project) == 1
    assert "obsolete key" in caplog.text


def test_declared_locale_without_catalog_fails(
    project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    write_catalog(fr_catalog(project), VALID)
    declare(project, "fr", "de")

    assert run(project) == 1
    assert "de: declared in locales.toml but has no catalog" in caplog.text


def test_undeclared_catalog_fails(project: Path, caplog: pytest.LogCaptureFixture) -> None:
    write_catalog(fr_catalog(project), VALID)
    declare(project)

    assert run(project) == 1
    assert "fr: catalog not declared" in caplog.text
    assert "no locale declared" in caplog.text


def test_invalid_locales_file_fails(project: Path) -> None:
    (project / "locales" / checker.LOCALES_FILE).write_text("supported = 3\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        run(project)


def test_plural_placeholders() -> None:
    assert checker.placeholders(("{count} domain", "{count} domains", "{{literal}}")) == {"count"}


def test_repository_catalogs_are_consistent() -> None:
    assert checker.main([]) == 0
