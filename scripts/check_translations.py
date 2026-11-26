# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check translation catalogs against the source code.

Fails when:
- the template (``messages.pot``) is out of date with the source code (missing or unused keys);
- a catalog lacks a key, has an empty translation, or keeps an obsolete key;
- a translation's named parameters differ from the source message.

Translations flagged ``needs-review`` (not yet validated by a native speaker) are only counted.

Usage: ``python scripts/check_translations.py [--locales DIR] [--source DIR]``.
"""

import argparse
import logging
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from babel.messages.catalog import Catalog, Message
from babel.messages.extract import extract_from_dir
from babel.messages.pofile import read_po

NEEDS_REVIEW = "needs-review"
PLACEHOLDER = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")
DEFAULT_LOCALES = Path("src/gandi_mcp/locales")
DEFAULT_SOURCE = Path("src")

logger = logging.getLogger("check_translations")


def message_key(message: Message) -> str:
    """Identify a message by its context and singular form."""
    identifier = message.id[0] if isinstance(message.id, tuple) else message.id
    return f"{message.context or ''}\x04{identifier}"


def placeholders(text: str | Iterable[str]) -> set[str]:
    """Return the named parameters used in a message or in all its plural forms."""
    texts = [text] if isinstance(text, str) else list(text)
    return {name for item in texts for name in PLACEHOLDER.findall(item)}


def read_catalog(path: Path) -> Catalog:
    """Read a PO or POT file."""
    with path.open("rb") as stream:
        return read_po(stream)


def source_keys(source: Path) -> set[str]:
    """Extract the message keys currently used in the source code."""
    keys: set[str] = set()
    for _filename, _lineno, message, _comments, context in extract_from_dir(
        str(source), method_map=[("**.py", "python")]
    ):
        identifier = message[0] if isinstance(message, tuple) else message
        keys.add(f"{context or ''}\x04{identifier}")
    return keys


def check_template(template: Catalog, used: set[str]) -> list[str]:
    """Compare the template with the keys used in the code."""
    declared = {message_key(message) for message in template if message.id}
    errors = [f"messages.pot lacks a key used in the code: {key!r}" for key in used - declared]
    errors += [f"messages.pot has an unused key: {key!r}" for key in declared - used]
    return errors


def check_catalog(language: str, catalog: Catalog, template: Catalog) -> tuple[list[str], int]:
    """Check one language against the template; return its errors and review count."""
    errors: list[str] = []
    expected = {message_key(message): message for message in template if message.id}
    actual = {message_key(message): message for message in catalog if message.id}
    errors += [f"{language}: missing key {key!r}" for key in expected.keys() - actual.keys()]
    errors += [f"{language}: unused key {key!r}" for key in actual.keys() - expected.keys()]
    errors += [
        f"{language}: obsolete key {key!r}" for key in map(message_key, catalog.obsolete.values())
    ]
    to_review = 0
    for key, message in actual.items():
        if key not in expected:
            continue
        string = message.string
        strings = [string] if isinstance(string, str) else list(string or ())
        if not all(strings):
            errors.append(f"{language}: empty translation for {key!r}")
            continue
        if placeholders(strings) != placeholders(expected[key].id):
            errors.append(f"{language}: parameters differ for {key!r}")
        if NEEDS_REVIEW in message.flags or any(NEEDS_REVIEW in c for c in message.user_comments):
            to_review += 1
    return errors, to_review


def run(locales: Path, source: Path) -> int:
    """Run every check and return the process exit code."""
    template = read_catalog(locales / "messages.pot")
    errors = check_template(template, source_keys(source))
    total_review = 0
    catalogs = sorted(locales.glob("*/LC_MESSAGES/messages.po"))
    if not catalogs:
        errors.append(f"no catalog found under {locales}")
    for path in catalogs:
        language_errors, to_review = check_catalog(
            path.parents[1].name, read_catalog(path), template
        )
        errors += language_errors
        total_review += to_review
    for error in errors:
        logger.error(error)
    logger.info(
        "%d languages checked, %d translations awaiting native review",
        len(catalogs),
        total_review,
    )
    return 1 if errors else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--locales", type=Path, default=DEFAULT_LOCALES)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    arguments = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    return run(arguments.locales, arguments.source)


if __name__ == "__main__":
    sys.exit(main())
