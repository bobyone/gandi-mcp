# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the UI catalog check, on temporary catalogs and on the real ones."""

import json
from pathlib import Path

import pytest

from scripts import check_ui_translations as check

SOURCE = {
    "app.title": "Gandi accounts",
    "accounts.count": "{count, plural, one {# account} other {# accounts}}",
    "feedback.saved": "The account {name} is saved.",
    "environment.production": "Production",
    "environment.sandbox": "Sandbox",
}
CODE = """
t("app.title"); t('accounts.count', { count }); t(`feedback.saved`, { name });
t(`environment.${account.environment}`);
"""


def write_ui(tmp_path: Path, catalogs: dict[str, dict[str, str]], code: str = CODE) -> Path:
    ui = tmp_path / "ui"
    (ui / "src" / "i18n" / "locales").mkdir(parents=True)
    (ui / "src" / "screen.tsx").write_text(code, encoding="utf-8")
    for language, catalog in catalogs.items():
        path = ui / "src" / "i18n" / "locales" / f"{language}.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
    (ui / "src" / "i18n" / "needs-review.json").write_text('{"fr": ["*"]}', encoding="utf-8")
    return ui


def write_locales(tmp_path: Path, locales: list[str]) -> Path:
    path = tmp_path / "locales.toml"
    path.write_text(f"supported = {json.dumps(locales)}\n", encoding="utf-8")
    return path


def french(**changes: str) -> dict[str, str]:
    catalog = {
        "app.title": "Comptes Gandi",
        "accounts.count": "{count, plural, one {# compte} other {# comptes}}",
        "feedback.saved": "Le compte {name} est enregistré.",
        "environment.production": "Production",
        "environment.sandbox": "Sandbox",
    }
    catalog.update(changes)
    return catalog


def test_valid_catalogs(tmp_path: Path) -> None:
    ui = write_ui(tmp_path, {"en": SOURCE, "fr": french(), "sr-Latn": french()})

    assert check.run(ui, write_locales(tmp_path, ["fr", "sr_Latn"])) == 0


def test_the_real_catalogs_are_valid() -> None:
    root = Path(__file__).resolve().parents[2]

    assert check.run(root / "ui", root / "src/gandi_mcp/locales/locales.toml") == 0


def test_source_keys_must_match_the_code() -> None:
    errors = check.check_source({**SOURCE, "old.key": "Old"}, [])
    assert "en: unused key 'old.key'" in errors

    literals, templates = check.used_keys([])
    assert (literals, templates) == (set(), [])


def test_detects_missing_unused_and_template_keys(tmp_path: Path) -> None:
    code = CODE + 't("missing.key"); t(`nothing.${x}`);'
    ui = write_ui(tmp_path, {"en": SOURCE, "fr": french()}, code)

    errors = check.check_source(SOURCE, sorted((ui / "src").rglob("*.ts*")))

    assert "en: missing key used in the code: 'missing.key'" in errors
    assert any("no key matches the template" in error for error in errors)


@pytest.mark.parametrize(
    ("catalog", "expected"),
    [
        ({k: v for k, v in french().items() if k != "app.title"}, "missing key 'app.title'"),
        (french(extra="Extra"), "unused key 'extra'"),
        (french(**{"app.title": " "}), "empty translation for 'app.title'"),
        (french(**{"feedback.saved": "Le compte {nom}."}), "arguments differ"),
        (
            french(**{"accounts.count": "{count, plural, one {# compte} many {# comptes}}"}),
            "plural without 'other'",
        ),
        (french(**{"accounts.count": "{count} comptes"}), "plural shape differs"),
    ],
)
def test_detects_catalog_errors(catalog: dict[str, str], expected: str) -> None:
    errors = check.check_catalog("fr", catalog, SOURCE)

    assert any(expected in error for error in errors), errors


def test_detects_missing_and_undeclared_languages(tmp_path: Path) -> None:
    ui = write_ui(tmp_path, {"en": SOURCE, "fr": french(), "xx": french()})

    assert check.run(ui, write_locales(tmp_path, ["fr", "de"])) == 1


def test_missing_english_catalog(tmp_path: Path) -> None:
    ui = write_ui(tmp_path, {"fr": french()})

    assert check.run(ui, write_locales(tmp_path, ["fr"])) == 1


def test_rejects_a_catalog_that_is_not_an_object(tmp_path: Path) -> None:
    path = tmp_path / "en.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(SystemExit):
        check.read_catalog(path)


def test_main(tmp_path: Path) -> None:
    ui = write_ui(tmp_path, {"en": SOURCE, "fr": french()})

    locales = str(write_locales(tmp_path, ["fr"]))
    glossary = tmp_path / "glossary.md"
    glossary.write_text(f"{check.GLOSSARY_START}\n{check.GLOSSARY_END}\n", encoding="utf-8")
    code = check.main(
        ["--ui", str(ui), "--locales", locales, "--glossary", str(glossary), "--write-glossary"]
    )

    assert code == 0


def test_glossary_labels_are_generated_and_checked(tmp_path: Path) -> None:
    glossary = tmp_path / "glossary.md"
    glossary.write_text(
        f"# Glossary\n\n{check.GLOSSARY_START}\nold\n{check.GLOSSARY_END}\n", encoding="utf-8"
    )
    catalogs = {"en": SOURCE, "fr": french()}

    assert check.check_glossary(glossary, catalogs, write=False) == [
        "glossary.md: UI labels are out of date (run with --write-glossary)"
    ]
    assert check.check_glossary(glossary, catalogs, write=True) == []
    assert check.check_glossary(glossary, catalogs, write=False) == []
    assert "| `fr` | " in glossary.read_text(encoding="utf-8")


def test_glossary_without_the_generated_section(tmp_path: Path) -> None:
    glossary = tmp_path / "glossary.md"
    glossary.write_text("# Glossary\n", encoding="utf-8")

    assert check.check_glossary(glossary, {}, write=True) == [
        "glossary.md: the generated UI labels section is missing"
    ]


def test_the_real_glossary_is_up_to_date() -> None:
    root = Path(__file__).resolve().parents[2]

    assert (
        check.run(
            root / "ui", root / "src/gandi_mcp/locales/locales.toml", root / "docs/glossary.md"
        )
        == 0
    )
