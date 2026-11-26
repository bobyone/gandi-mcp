# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the local page server, over real HTTP on 127.0.0.1."""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx2
import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.pending_confirmation import PendingConfirmation
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.gandi.exceptions import GandiUnavailableError
from gandi_mcp.i18n.babel.babel_translator import BabelTranslator, default_locales_directory
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.local_pages.starlette.starlette_local_page_server import (
    StarletteLocalPageServer,
)
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.token_entry_session import TokenEntrySession
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget, TokenPurpose
from gandi_mcp.token_entry.token_submission import TokenSubmission
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
FORM = {"Content-Type": "application/x-www-form-urlencoded"}


class Clock:
    def __init__(self) -> None:
        self.now = 10.0

    def __call__(self) -> float:
        return self.now


@dataclass
class Pages:
    server: StarletteLocalPageServer
    sessions: TokenEntrySessions
    pending: PendingConfirmations
    accounts: AccountService
    secrets: InMemorySecretStore
    preferences: InMemoryPreferencesStore
    verifier: StubTokenVerifier
    clock: Clock
    http: httpx2.AsyncClient

    async def token_page(self, name: str = "Perso", locale: str | None = "fr") -> str:
        target = TokenEntryTarget(TokenPurpose.ADD, AccountName(name), Environment.SANDBOX)
        session = self.sessions.open(target)
        return await self.server.open_token_entry(session, locale)

    async def confirmation_page(self) -> tuple[PendingConfirmation, str]:
        request = ConfirmationRequest(
            "domain.delete:example.com",
            OperationCategory.DESTRUCTIVE,
            LocalizedText(Message("delete {domain}"), {"domain": "<b>example.com</b>"}),
            AccountName("Pro"),
            Environment.PRODUCTION,
        )
        pending = self.pending.create(request)
        return pending, await self.server.open_confirmation(pending, "en")


@pytest.fixture
async def pages() -> AsyncIterator[Pages]:
    clock = Clock()
    preferences, secrets, verifier = (
        InMemoryPreferencesStore(),
        InMemorySecretStore(),
        StubTokenVerifier(),
    )
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(preferences, secrets, verifier)
    sessions, pending = TokenEntrySessions(600, clock), PendingConfirmations(300, clock)
    server = StarletteLocalPageServer(
        pending,
        sessions,
        TokenSubmission(accounts),
        BabelTranslator(default_locales_directory()),
        page_timeout_seconds=600,
        clock=clock,
    )
    async with httpx2.AsyncClient(timeout=10, trust_env=False) as http:
        yield Pages(
            server, sessions, pending, accounts, secrets, preferences, verifier, clock, http
        )
    await server.close()


def code_of(url: str) -> str:
    return url.rsplit("/", 1)[1]


async def test_url_is_local_with_a_secret_code(pages: Pages) -> None:
    url = await pages.token_page()

    assert re.fullmatch(r"http://127\.0\.0\.1:\d+/token/[A-Za-z0-9_-]{43}", url)


def _target() -> TokenEntryTarget:
    return TokenEntryTarget(TokenPurpose.ADD, AccountName("X"), Environment.SANDBOX)


async def test_token_form_is_translated_and_hardened(pages: Pages) -> None:
    url = await pages.token_page(locale="fr")

    response = await pages.http.get(url)

    assert response.status_code == 200
    assert '<html lang="fr">' in response.text
    assert "du compte de test (sandbox) Perso." in response.text
    assert 'type="password"' in response.text
    assert "<script" not in response.text
    assert re.findall(r'<a href="([^"]*)"', response.text) == ["https://admin.sandbox.gandi.net/"]
    headers = response.headers
    assert "default-src 'none'" in headers["content-security-policy"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert headers["referrer-policy"] == "same-origin"
    assert headers["cache-control"] == "no-store"
    assert headers["x-frame-options"] == "DENY"
    assert "server" not in headers


async def test_submitting_a_token_adds_the_account_once(pages: Pages) -> None:
    url = await pages.token_page()
    body = {"code": code_of(url), "token": TOKEN.reveal()}

    first = await pages.http.post(url, data=body)
    second = await pages.http.post(url, data=body)

    assert first.status_code == 200
    assert "ada" in first.text
    assert TOKEN.reveal() not in first.text
    assert [str(a.name) for a in await pages.accounts.list()] == ["Perso"]
    assert second.status_code == 410


async def test_invalid_format_keeps_the_session_open(pages: Pages) -> None:
    url = await pages.token_page()

    refused = await pages.http.post(url, data={"code": code_of(url), "token": "short"})
    accepted = await pages.http.post(url, data={"code": code_of(url), "token": TOKEN.reveal()})

    assert refused.status_code == 422
    assert 'role="alert"' in refused.text
    assert "short" not in refused.text
    assert accepted.status_code == 200


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ("rejected", "Gandi"),
        ("duplicate", "Perso"),
        ("keyring", "keyring"),
        ("preferences", "preferences"),
        ("gandi", "Gandi"),
    ],
)
async def test_submission_failures_are_explained(pages: Pages, setup: str, expected: str) -> None:
    url = await pages.token_page(locale=None)
    token = TOKEN
    if setup == "rejected":
        token = PersonalAccessToken("pat_unknown_0123456789")
    elif setup == "duplicate":
        await pages.accounts.add(AccountDraft(AccountName("perso"), Environment.SANDBOX), TOKEN)
    elif setup == "keyring":
        pages.secrets.unavailable = True
    elif setup == "preferences":
        pages.preferences.fail_on_save = True
    else:
        pages.verifier.failure = GandiUnavailableError("down")

    response = await pages.http.post(
        url,
        data={"code": code_of(url), "token": token.reveal()},
        headers={"Accept-Language": "en-GB;q=0.9, *;q=0.1"},
    )

    assert response.status_code == 422
    assert expected in response.text
    assert token.reveal() not in response.text


async def test_account_gone_before_replacing(pages: Pages) -> None:
    target = TokenEntryTarget(TokenPurpose.REPLACE, AccountName("Gone"), Environment.SANDBOX)
    url = await pages.server.open_token_entry(pages.sessions.open(target), None)

    response = await pages.http.post(url, data={"code": code_of(url), "token": TOKEN.reveal()})

    assert response.status_code == 422
    assert "Gone" in response.text


async def test_browser_form_submission_is_accepted(pages: Pages) -> None:
    url = await pages.token_page()
    origin = pages.server.origin
    assert origin is not None
    headers = {"Origin": origin, "Sec-Fetch-Site": "same-origin", "Referer": url}

    response = await pages.http.post(
        url, data={"code": code_of(url), "token": TOKEN.reveal()}, headers=headers
    )

    assert response.status_code == 200
    assert [str(a.name) for a in await pages.accounts.list()] == ["Perso"]


@pytest.mark.parametrize(
    ("headers", "body_code"),
    [
        ({"Host": "evil.example"}, True),
        ({"Host": "localhost"}, True),
        ({"Origin": "http://evil.example"}, True),
        ({"Origin": "null"}, True),
        ({"Sec-Fetch-Site": "cross-site"}, True),
        ({}, False),
    ],
)
async def test_untrusted_requests_are_refused(
    pages: Pages, headers: dict[str, str], body_code: bool
) -> None:
    url = await pages.token_page()
    body = {"code": code_of(url) if body_code else "wrong", "token": TOKEN.reveal()}

    response = await pages.http.post(url, data=body, headers=headers)

    assert response.status_code in {400, 403}
    assert await pages.accounts.list() == ()


async def test_other_content_types_and_oversized_bodies_are_refused(pages: Pages) -> None:
    url = await pages.token_page()

    as_json = await pages.http.post(url, json={"code": code_of(url), "token": TOKEN.reveal()})
    oversized = await pages.http.post(url, content=b"code=" + b"x" * 9000, headers=FORM)
    duplicated = await pages.http.post(
        url, content=f"code={code_of(url)}&code=x&token={TOKEN.reveal()}".encode(), headers=FORM
    )
    undecodable = await pages.http.post(url, content=b"code=\xff", headers=FORM)

    assert {as_json.status_code, oversized.status_code, duplicated.status_code} == {400}
    assert undecodable.status_code == 400
    assert await pages.accounts.list() == ()


async def test_unknown_and_expired_pages(pages: Pages) -> None:
    url = await pages.token_page()
    unknown = url.rsplit("/", 1)[0] + "/unknown"
    wrong_kind = url.replace("/token/", "/confirm/")

    assert (await pages.http.get(unknown)).status_code == 410
    assert (await pages.http.get(wrong_kind)).status_code == 410
    pages.clock.now += 601
    assert (await pages.http.get(url)).status_code == 410


async def test_session_expired_while_the_page_is_open(pages: Pages) -> None:
    url = await pages.token_page()
    for session in list(pages.sessions._sessions.values()):  # test setup: drop the session
        pages.sessions.close(session.session_id)

    response = await pages.http.post(url, data={"code": code_of(url), "token": TOKEN.reveal()})

    assert response.status_code == 410


async def test_confirmation_page_escapes_untrusted_data(pages: Pages) -> None:
    _pending, url = await pages.confirmation_page()

    response = await pages.http.get(url)

    assert response.status_code == 200
    assert "&lt;b&gt;example.com&lt;/b&gt;" in response.text
    assert "<b>example.com" not in response.text
    assert "production" in response.text


@pytest.mark.parametrize(("decision", "accepted"), [("confirm", True), ("refuse", False)])
async def test_confirmation_is_answered_once(pages: Pages, decision: str, accepted: bool) -> None:
    pending, url = await pages.confirmation_page()
    body = {"code": code_of(url), "decision": decision}

    first = await pages.http.post(url, data=body)
    second = await pages.http.post(url, data=body)

    assert first.status_code == 200
    assert second.status_code == 410
    subject = pending.request.subject
    if accepted:
        assert pages.pending.consume(pending.confirmation_id, subject)
    else:
        with pytest.raises(Exception, match="refused"):
            pages.pending.consume(pending.confirmation_id, subject)


async def test_confirmation_with_an_unknown_decision(pages: Pages) -> None:
    pending, url = await pages.confirmation_page()

    response = await pages.http.post(url, data={"code": code_of(url), "decision": "maybe"})

    assert response.status_code == 400
    assert not pages.pending.consume(pending.confirmation_id, pending.request.subject)


async def test_confirmation_expired_while_the_page_is_open(pages: Pages) -> None:
    pending, url = await pages.confirmation_page()
    pages.pending.cancel(pending.confirmation_id)

    get = await pages.http.get(url)

    assert get.status_code == 410


async def test_confirmation_answered_elsewhere(pages: Pages) -> None:
    pending, url = await pages.confirmation_page()
    pages.pending.answer(pending.confirmation_id, True)

    response = await pages.http.post(url, data={"code": code_of(url), "decision": "refuse"})

    assert response.status_code == 410


async def test_server_stops_when_idle_and_restarts(pages: Pages) -> None:
    await pages.token_page()
    first_origin = pages.server.origin
    pages.clock.now += 601
    await pages.server._stop_when_idle()

    assert pages.server.origin is None
    url = await pages.token_page()
    assert pages.server.origin is not None
    assert first_origin is not None
    assert (await pages.http.get(url)).status_code == 200


async def test_session_object_is_not_exposed(pages: Pages) -> None:
    session: TokenEntrySession = pages.sessions.open(_target())
    url = await pages.server.open_token_entry(session, None)

    assert session.session_id not in url


async def test_account_moved_while_the_replacement_page_is_open(pages: Pages) -> None:
    await pages.accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    account = await pages.accounts.resolve(AccountName("Perso"))
    target = TokenEntryTarget(
        TokenPurpose.REPLACE, account.name, account.environment, expected=account.reference
    )
    url = await pages.server.open_token_entry(pages.sessions.open(target), None)
    production = PersonalAccessToken("pat_production_01234567")
    pages.verifier.accept(Environment.PRODUCTION, production)
    await pages.accounts.change_environment(account.name, Environment.PRODUCTION, production)
    calls = len(pages.verifier.calls)

    response = await pages.http.post(url, data={"code": code_of(url), "token": TOKEN.reveal()})

    assert response.status_code == 422
    assert "moved to another environment" in response.text
    assert len(pages.verifier.calls) == calls
    assert pages.secrets.tokens[account.secret_key] == production
