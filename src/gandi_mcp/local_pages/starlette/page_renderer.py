# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""HTML of the local pages: escaped text, no script, one inline style sheet."""

import base64
import hashlib
from dataclasses import dataclass
from html import escape

STYLE = (
    "body{font-family:system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem;"
    "line-height:1.5;color:#1b1b1b;background:#fff}"
    "@media (prefers-color-scheme:dark){body{color:#eee;background:#161616}a{color:#8ab4f8}}"
    "label{display:block;font-weight:600;margin:1rem 0 .25rem}"
    "input[type=password]{width:100%;box-sizing:border-box;padding:.5rem;font:inherit}"
    "button{margin:1rem .5rem 0 0;padding:.5rem 1.25rem;font:inherit;cursor:pointer}"
    ".alert{padding:.75rem 1rem;border-left:.25rem solid #b00020;background:#fdecee;color:#5f0010}"
    ".ok{border-left-color:#1e7e34;background:#e8f5ea;color:#0b3d17}"
)
STYLE_HASH = base64.b64encode(hashlib.sha256(STYLE.encode("utf-8")).digest()).decode("ascii")
CONTENT_SECURITY_POLICY = (
    f"default-src 'none'; style-src 'sha256-{STYLE_HASH}'; form-action 'self'; "
    "frame-ancestors 'none'; base-uri 'none'"
)


@dataclass(frozen=True)
class TokenForm:
    """Texts and fields of the token entry form, already translated."""

    title: str
    intro: str
    label: str
    help_text: str
    help_url: str
    submit: str
    code: str
    error: str | None = None


@dataclass(frozen=True)
class ConfirmationForm:
    """Texts and fields of the confirmation form, already translated."""

    title: str
    question: str
    confirm: str
    refuse: str
    code: str


def _document(language: str, title: str, body: str) -> str:
    return (
        f'<!doctype html><html lang="{escape(language)}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta name="referrer" content="same-origin"><title>{escape(title)}</title>'
        f"<style>{STYLE}</style></head><body><main><h1>{escape(title)}</h1>{body}</main>"
        "</body></html>"
    )


def html_language(locale: str) -> str:
    """Turn a CLDR locale (``sr_Latn``) into a BCP 47 tag (``sr-Latn``)."""
    return locale.replace("_", "-")


def token_page(language: str, form: TokenForm) -> str:
    """Render the token entry form."""
    error = (
        f'<p class="alert" role="alert">{escape(form.error)}</p>' if form.error is not None else ""
    )
    body = (
        f"{error}<p>{escape(form.intro)}</p>"
        '<form method="post" autocomplete="off">'
        f'<input type="hidden" name="code" value="{escape(form.code)}">'
        f'<label for="token">{escape(form.label)}</label>'
        '<input type="password" id="token" name="token" required minlength="16" '
        'maxlength="512" spellcheck="false" autocapitalize="off" autofocus>'
        f'<p><a href="{escape(form.help_url)}" target="_blank" rel="noopener noreferrer">'
        f"{escape(form.help_text)}</a></p>"
        f'<button type="submit">{escape(form.submit)}</button></form>'
    )
    return _document(language, form.title, body)


def confirmation_page(language: str, form: ConfirmationForm) -> str:
    """Render the confirmation form with its two buttons."""
    body = (
        f"<p>{escape(form.question)}</p>"
        '<form method="post">'
        f'<input type="hidden" name="code" value="{escape(form.code)}">'
        f'<button type="submit" name="decision" value="confirm">{escape(form.confirm)}</button>'
        f'<button type="submit" name="decision" value="refuse">{escape(form.refuse)}</button>'
        "</form>"
    )
    return _document(language, form.title, body)


def outcome_page(language: str, title: str, message: str, success: bool) -> str:
    """Render the outcome of a submission."""
    kind = "alert ok" if success else "alert"
    role = "status" if success else "alert"
    return _document(language, title, f'<p class="{kind}" role="{role}">{escape(message)}</p>')
