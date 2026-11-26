# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Local page server on Starlette, run by an embedded Uvicorn server on 127.0.0.1."""

import asyncio
import contextlib
import hmac
import logging
import secrets
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qs

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import (
    AccountChangedError,
    AccountNotFoundError,
    DuplicateAccountError,
    NoAccountError,
    TokenRejectedError,
)
from gandi_mcp.confirmation.exceptions import ConfirmationError
from gandi_mcp.confirmation.messages import confirmation_prompt
from gandi_mcp.confirmation.pending_confirmation import PendingConfirmation
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.gandi.exceptions import GandiError
from gandi_mcp.i18n.message import Message
from gandi_mcp.i18n.translator import Translator
from gandi_mcp.local_pages import messages
from gandi_mcp.local_pages.local_page_server import LocalPageServer
from gandi_mcp.local_pages.starlette.page_renderer import (
    CONTENT_SECURITY_POLICY,
    ConfirmationForm,
    TokenForm,
    confirmation_page,
    html_language,
    outcome_page,
    token_page,
)
from gandi_mcp.preferences.exceptions import PreferencesError
from gandi_mcp.secrets.exceptions import InvalidTokenFormatError, SecretStoreError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.exceptions import TokenEntryError
from gandi_mcp.token_entry.token_entry_session import TokenEntrySession
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_submission import TokenSubmission

HOST = "127.0.0.1"
MAX_BODY = 8192
STARTUP_TIMEOUT = 10.0
ADMIN_URLS = {
    Environment.PRODUCTION: "https://admin.gandi.net/",
    Environment.SANDBOX: "https://admin.sandbox.gandi.net/",
}
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
}

logger = logging.getLogger(__name__)


class PageKind(StrEnum):
    """The two kinds of local pages."""

    TOKEN = "token"  # noqa: S105 - URL path segment, not a secret
    CONFIRMATION = "confirm"


@dataclass(frozen=True)
class _Page:
    kind: PageKind
    reference: str
    locale: str | None
    deadline: float


class _EmbeddedServer(uvicorn.Server):
    """Uvicorn server that leaves the signal handlers of the MCP server alone."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None]:
        yield


class StarletteLocalPageServer(LocalPageServer):
    """Serve the local pages, starting on demand and stopping when none is open.

    Requests are refused unless their ``Host`` is this server, their ``Origin`` (when
    sent) is this server, and their form repeats the page code. Pages carry no
    script; responses forbid framing, caching and referrers.
    """

    def __init__(
        self,
        pending: PendingConfirmations,
        sessions: TokenEntrySessions,
        submission: TokenSubmission,
        translator: Translator,
        *,
        page_timeout_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Configure the server.

        Args:
            pending: Pending confirmations answered on confirmation pages.
            sessions: Token entry sessions used by token pages.
            submission: Applies a submitted token to its account.
            translator: Translates the pages.
            page_timeout_seconds: Longest validity of a page (the longest of the
                confirmation and token entry timeouts).
            clock: Monotonic clock, for tests.
        """
        self._pending = pending
        self._sessions = sessions
        self._submission = submission
        self._translator = translator
        self._page_timeout = page_timeout_seconds
        self._clock = clock
        self._pages: dict[str, _Page] = {}
        self._server: _EmbeddedServer | None = None
        self._task: asyncio.Task[None] | None = None
        self._port: int | None = None
        self._lock = asyncio.Lock()
        self._app = Starlette(
            routes=[
                Route("/token/{code}", self._token, methods=["GET", "POST"]),
                Route("/confirm/{code}", self._confirmation, methods=["GET", "POST"]),
            ]
        )

    @property
    def app(self) -> Starlette:
        """The ASGI application, for in-process tests."""
        return self._app

    @property
    def origin(self) -> str | None:
        """``http://127.0.0.1:<port>`` while the server runs."""
        return f"http://{HOST}:{self._port}" if self._port is not None else None

    async def open_token_entry(self, session: TokenEntrySession, locale: str | None) -> str:
        return await self._register(PageKind.TOKEN, session.session_id, locale)

    async def open_confirmation(self, pending: PendingConfirmation, locale: str | None) -> str:
        return await self._register(PageKind.CONFIRMATION, pending.confirmation_id, locale)

    async def close(self) -> None:
        async with self._lock:
            self._pages.clear()
            await self._stop()

    async def _register(self, kind: PageKind, reference: str, locale: str | None) -> str:
        async with self._lock:
            self._purge()
            await self._start()
            code = secrets.token_urlsafe(32)
            self._pages[code] = _Page(kind, reference, locale, self._clock() + self._page_timeout)
            asyncio.get_running_loop().call_later(
                self._page_timeout + 1, lambda: asyncio.ensure_future(self._stop_when_idle())
            )
            return f"{self.origin}/{kind.value}/{code}"

    async def _start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        config = uvicorn.Config(
            self._app,
            host=HOST,
            port=0,
            log_config=None,
            access_log=False,
            lifespan="off",
            server_header=False,
            date_header=False,
        )
        server = _EmbeddedServer(config)
        task = asyncio.create_task(server.serve())
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while not server.started:
            if task.done() or time.monotonic() > deadline:
                task.cancel()
                raise OSError("the local page server could not start")
            await asyncio.sleep(0.01)
        self._server, self._task = server, task
        self._port = int(server.servers[0].sockets[0].getsockname()[1])
        logger.info("local page server started")

    async def _stop(self) -> None:
        if self._server is not None and self._task is not None:
            self._server.should_exit = True
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            logger.info("local page server stopped")
        self._server, self._task, self._port = None, None, None

    async def _stop_when_idle(self) -> None:
        async with self._lock:
            self._purge()
            if not self._pages:
                await self._stop()

    def _purge(self) -> None:
        now = self._clock()
        for code in [code for code, page in self._pages.items() if now > page.deadline]:
            del self._pages[code]

    def _text(self, locale: str, message: Message, **params: object) -> str:
        return self._translator.translate(message, locale, **params)

    def _locale(self, request: Request, page: _Page | None) -> str:
        if page is not None and page.locale:
            return self._translator.negotiate([page.locale])
        header = request.headers.get("accept-language", "")
        ranked = []
        for part in header.split(",")[:20]:
            tag, _, quality = part.strip().partition(";q=")
            try:
                weight = float(quality) if quality else 1.0
            except ValueError:
                continue
            if tag and tag != "*":
                ranked.append((weight, tag))
        ranked.sort(key=lambda item: -item[0])
        return self._translator.negotiate([tag for _, tag in ranked])

    def _respond(self, body: str, status: int = 200) -> Response:
        return HTMLResponse(body, status_code=status, headers=SECURITY_HEADERS)

    def _outcome(
        self,
        locale: str,
        kind: PageKind,
        message: Message,
        success: bool,
        status: int = 200,
        **params: object,
    ) -> Response:
        title = messages.TITLE_TOKEN if kind is PageKind.TOKEN else messages.TITLE_CONFIRMATION
        return self._respond(
            outcome_page(
                html_language(locale),
                self._text(locale, title),
                self._text(locale, message, **params),
                success,
            ),
            status,
        )

    def _trusted(self, request: Request) -> bool:
        expected = f"{HOST}:{self._port}"
        if request.headers.get("host") != expected:
            return False
        if request.method == "POST":
            origin = request.headers.get("origin")
            if origin is not None and origin != f"http://{expected}":
                return False
            site = request.headers.get("sec-fetch-site")
            if site is not None and site not in {"same-origin", "none"}:
                return False
        return True

    async def _form(self, request: Request) -> dict[str, str] | None:
        if request.headers.get("content-type", "").split(";")[0].strip() != (
            "application/x-www-form-urlencoded"
        ):
            return None
        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > MAX_BODY:
                return None
        try:
            fields = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=4)
        except (UnicodeDecodeError, ValueError):
            return None
        return {key: values[0] for key, values in fields.items() if len(values) == 1}

    def _page(self, code: str, kind: PageKind) -> _Page | None:
        page = self._pages.get(code)
        if page is None or page.kind is not kind:
            return None
        if self._clock() > page.deadline:
            del self._pages[code]
            return None
        return page

    async def _checked(
        self, request: Request, kind: PageKind
    ) -> tuple[str, _Page | None, dict[str, str] | None, Response | None]:
        code = request.path_params["code"]
        page = self._page(code, kind)
        locale = self._locale(request, page)
        if not self._trusted(request):
            return (
                code,
                None,
                None,
                self._outcome(locale, kind, messages.REQUEST_REFUSED, False, 403),
            )
        if page is None:
            return code, None, None, self._outcome(locale, kind, messages.PAGE_EXPIRED, False, 410)
        if request.method == "GET":
            return code, page, None, None
        form = await self._form(request)
        if form is None or not hmac.compare_digest(form.get("code", ""), code):
            return (
                code,
                None,
                None,
                self._outcome(locale, kind, messages.REQUEST_REFUSED, False, 400),
            )
        return code, page, form, None

    async def _token(self, request: Request) -> Response:
        code, page, form, refusal = await self._checked(request, PageKind.TOKEN)
        if refusal is not None or page is None:
            return refusal or self._respond("", 500)
        locale = self._locale(request, page)
        try:
            session = self._sessions.peek(page.reference)
        except TokenEntryError:
            self._pages.pop(code, None)
            return self._outcome(locale, PageKind.TOKEN, messages.PAGE_EXPIRED, False, 410)
        if form is None:
            return self._token_form(locale, code, session)
        try:
            token = PersonalAccessToken(form.get("token", "").strip())
        except InvalidTokenFormatError:
            return self._token_form(locale, code, session, messages.INVALID_TOKEN, 422)
        self._pages.pop(code, None)
        try:
            self._sessions.use(session.session_id)
        except TokenEntryError:
            return self._outcome(locale, PageKind.TOKEN, messages.PAGE_EXPIRED, False, 410)
        return await self._submit(locale, session, token)

    def _token_form(
        self,
        locale: str,
        code: str,
        session: TokenEntrySession,
        error: Message | None = None,
        status: int = 200,
    ) -> Response:
        target = session.target
        intro = (
            messages.TOKEN_INTRO_PRODUCTION
            if target.environment is Environment.PRODUCTION
            else messages.TOKEN_INTRO_SANDBOX
        )
        form = TokenForm(
            title=self._text(locale, messages.TITLE_TOKEN),
            intro=self._text(locale, intro, account=str(target.name)),
            label=self._text(locale, messages.TOKEN_LABEL),
            help_text=self._text(locale, messages.TOKEN_HELP),
            help_url=ADMIN_URLS[target.environment],
            submit=self._text(locale, messages.SAVE),
            code=code,
            error=self._text(locale, error) if error is not None else None,
        )
        return self._respond(token_page(html_language(locale), form), status)

    async def _submit(
        self, locale: str, session: TokenEntrySession, token: PersonalAccessToken
    ) -> Response:
        account = str(session.target.name)
        failure: Message | None = None
        try:
            verified = await self._submission.submit(session.target, token)
        except TokenRejectedError:
            failure = messages.TOKEN_REJECTED
        except AccountChangedError:
            failure = messages.ACCOUNT_CHANGED
        except DuplicateAccountError:
            failure = messages.DUPLICATE_ACCOUNT
        except (AccountNotFoundError, NoAccountError):
            failure = messages.ACCOUNT_GONE
        except SecretStoreError:
            failure = messages.KEYRING_UNAVAILABLE
        except PreferencesError:
            failure = messages.PREFERENCES_UNAVAILABLE
        except GandiError:
            failure = messages.GANDI_UNAVAILABLE
        if failure is not None:
            logger.info("token entry failed: %s", failure.singular.split(".")[0])
            return self._outcome(locale, PageKind.TOKEN, failure, False, 422, account=account)
        return self._outcome(
            locale,
            PageKind.TOKEN,
            messages.SAVED,
            True,
            account=account,
            username=verified.identity.username,
        )

    async def _confirmation(self, request: Request) -> Response:
        code, page, form, refusal = await self._checked(request, PageKind.CONFIRMATION)
        if refusal is not None or page is None:
            return refusal or self._respond("", 500)
        locale = self._locale(request, page)
        try:
            pending = self._pending.get(page.reference)
        except ConfirmationError:
            self._pages.pop(code, None)
            return self._outcome(locale, PageKind.CONFIRMATION, messages.PAGE_EXPIRED, False, 410)
        if form is None:
            question = confirmation_prompt(self._translator, pending.request, locale)
            confirmation_form = ConfirmationForm(
                title=self._text(locale, messages.TITLE_CONFIRMATION),
                question=question,
                confirm=self._text(locale, messages.CONFIRM),
                refuse=self._text(locale, messages.REFUSE),
                code=code,
            )
            return self._respond(confirmation_page(html_language(locale), confirmation_form))
        decision = form.get("decision")
        if decision not in {"confirm", "refuse"}:
            return self._outcome(
                locale, PageKind.CONFIRMATION, messages.REQUEST_REFUSED, False, 400
            )
        self._pages.pop(code, None)
        try:
            self._pending.answer(pending.confirmation_id, decision == "confirm")
        except ConfirmationError:
            return self._outcome(locale, PageKind.CONFIRMATION, messages.PAGE_EXPIRED, False, 410)
        accepted = decision == "confirm"
        return self._outcome(
            locale,
            PageKind.CONFIRMATION,
            messages.CONFIRMED if accepted else messages.REFUSED,
            accepted,
        )
