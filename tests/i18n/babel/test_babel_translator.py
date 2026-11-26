# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the Babel translator, on temporary catalogs and on the shipped ones."""

from pathlib import Path

import pytest
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po

from gandi_mcp.i18n.babel.babel_translator import BabelTranslator, default_locales_directory
from gandi_mcp.i18n.exceptions import TranslationError
from gandi_mcp.i18n.message import N_, ngettext

GREETING = N_("Hello {name}")
ACCOUNTS = ngettext("{count} account", "{count} accounts")


def write_catalog(directory: Path, locale: str, entries: dict[object, object]) -> None:
    catalog = Catalog(locale=locale)
    for identifier, string in entries.items():
        catalog.add(identifier, string)  # type: ignore[arg-type]
    target = directory / locale / "LC_MESSAGES"
    target.mkdir(parents=True)
    with (target / "messages.po").open("wb") as stream:
        write_po(stream, catalog)


@pytest.fixture
def locales(tmp_path: Path) -> Path:
    (tmp_path / "locales.toml").write_text(
        'supported = ["fr", "sr_Latn", "pl"]\n', encoding="utf-8"
    )
    write_catalog(
        tmp_path,
        "fr",
        {
            "Hello {name}": "Bonjour {name}",
            ("{count} account", "{count} accounts"): (
                "{count} compte",
                "{count} de comptes",
                "{count} comptes",
            ),
        },
    )
    write_catalog(tmp_path, "sr_Latn", {"Hello {name}": "Zdravo {name}"})
    write_catalog(
        tmp_path,
        "pl",
        {
            ("{count} account", "{count} accounts"): (
                "{count} konto",
                "{count} konta",
                "{count} kont",
            )
        },
    )
    return tmp_path


def test_translates_with_named_parameters(locales: Path) -> None:
    translator = BabelTranslator(locales)

    assert translator.translate(GREETING, "fr", name="Ada") == "Bonjour Ada"
    assert translator.translate(GREETING, name="Ada") == "Hello Ada"


def test_default_locale_comes_from_the_system(locales: Path) -> None:
    translator = BabelTranslator(locales, default_locale="fr_FR")

    assert translator.default_locale == "fr"
    assert translator.translate(GREETING, name="Ada") == "Bonjour Ada"


@pytest.mark.parametrize(
    ("count", "expected"), [(1, "1 konto"), (3, "3 konta"), (5, "5 kont"), (22, "22 konta")]
)
def test_uses_the_plural_rules_of_the_language(locales: Path, count: int, expected: str) -> None:
    assert BabelTranslator(locales).translate(ACCOUNTS, "pl", count=count) == expected


def test_formats_numbers_for_the_locale(locales: Path) -> None:
    translator = BabelTranslator(locales)

    expected = "1\N{NARROW NO-BREAK SPACE}234 comptes"
    assert translator.translate(ACCOUNTS, "fr", count=1234) == expected
    assert translator.translate(GREETING, "en", name=1234.5) == "Hello 1,234.5"


def test_untranslated_message_falls_back_to_english(locales: Path) -> None:
    assert BabelTranslator(locales).translate(GREETING, "pl", name="Ada") == "Hello Ada"


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        (["fr-CA"], "fr"),
        (["FR"], "fr"),
        (["sr-Latn-RS"], "sr_Latn"),
        (["cnr"], "sr_Latn"),
        (["zz", "pl-PL"], "pl"),
        (["de", "it"], "en"),
        (["en-GB"], "en"),
        ([""], "en"),
        ([], "en"),
    ],
)
def test_negotiates_the_closest_locale(locales: Path, tags: list[str], expected: str) -> None:
    assert BabelTranslator(locales).negotiate(tags) == expected


def test_lists_supported_locales(locales: Path) -> None:
    assert BabelTranslator(locales).supported_locales == ("en", "fr", "pl", "sr_Latn")


def test_missing_parameter_is_an_error(locales: Path) -> None:
    with pytest.raises(TranslationError, match="name"):
        BabelTranslator(locales).translate(GREETING, "fr")


@pytest.mark.parametrize("count", [None, "2", True])
def test_plural_needs_an_integer_count(locales: Path, count: object) -> None:
    with pytest.raises(TranslationError):
        BabelTranslator(locales).translate(ACCOUNTS, "fr", count=count)


@pytest.mark.parametrize(
    "declaration", ["supported = [", 'supported = "fr"\n', "supported = [1]\n"]
)
def test_rejects_an_invalid_declaration(tmp_path: Path, declaration: str) -> None:
    (tmp_path / "locales.toml").write_text(declaration, encoding="utf-8")

    with pytest.raises(TranslationError):
        BabelTranslator(tmp_path)


def test_rejects_a_missing_catalog(tmp_path: Path) -> None:
    (tmp_path / "locales.toml").write_text('supported = ["fr"]\n', encoding="utf-8")

    with pytest.raises(TranslationError, match="fr"):
        BabelTranslator(tmp_path)


def test_loads_every_shipped_catalog() -> None:
    translator = BabelTranslator(default_locales_directory())

    assert len(translator.supported_locales) == 43
    assert translator.negotiate(["cnr"]) == "cnr"
    assert translator.negotiate(["sr"]) == "sr_Cyrl"
    assert translator.negotiate(["no"]) == "nb"
