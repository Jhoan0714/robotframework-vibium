"""Browser, context and page orchestration for the Robot Framework library.

This module is **not** a copy of Vibium's client API (``vibium.browser`` /
``Browser``). The upstream client exposes primitives such as ``start``,
``new_page``, ``new_context``, and ``pages``; it does **not** maintain the
Robot-facing notions of:

- Which browser instance is globally "active"
- Which :class:`BrowserContext` is active inside a browser
- Which :class:`Page` is active for keywords that omit handles
- How to validate that a context or page handle belongs to **this** Python
  library instance across **multiple** open browsers

**Layers**

:class:`BrowserSession`
    Tracks exactly **one** Vibium browser process worth of local state:

    - The current ``context`` and ``page`` that keywords should treat as active
      for that browser unless an explicit scope/handle is passed.
    - A registry of contexts the library knows about (``_contexts``): created
      via ``new_context`` or inferred when binding a page whose parent context
      was not previously listed.
    - A map of **last remembered** active page **per parent context identity**
      (``_active_page_by_context``, keyed by ``id(context)``). Used by
      :meth:`BrowserSession.switch_context` and by helpers such as resolving
      which page should back cookie/storage keywords for a given context handle.

:class:`SessionPool`
    Owns ``N`` instances of :class:`BrowserSession` (one per ``Open Browser``).
    Keywords that do not pass ``browser=`` rely on mirrored global fields:

    - ``browser``, ``context``, ``page``: the "active triple" pointing at objects
      on whichever session last completed a mutation, or—as a special rule—after
      :meth:`SessionPool.close` on one browser, the **last remaining** opened
      session (order is creation order).

    The pool maintains reverse lookup tables (see ``_by_*``) so that resolving
    an explicit ``context`` or ``page`` handle to its owning session is cheap
    and does not repeatedly scan RPC lists.

**Synchronisation contract**

After any pool operation that can change contexts or pages inside a browser,
:meth:`SessionPool._after_mutation` runs for the affected session: purge stale
reverse-map entries for that session, rebuild indices from the session's honest
local state, then copy ``browser/context/page`` from that session into the
pool globals. New public methods **should** funnel through ``_mutate_session`` /
``_mutate_browser`` or explicitly call ``_after_mutation`` exactly once per
successful mutation unless there is a very strong reason not to.

**Limitations**

- Contexts/pages created only inside the browser UI (outside library calls), or
  via upstream event hooks not wired here, might not appear in ``_contexts`` or
  indices until something in the library registers or binds them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import BrowserSessionError


@dataclass
class BrowserSession:
    """Local coordinator for exactly one running Vibium browser instance.

    Wraps objects returned by Vibium (sync ``vibium.browser.start`` flows) while
    adding **explicit state** Robot needs: active context/page, bookkeeping for
    user contexts (:class:`~vibium.sync_api.context.BrowserContext` or async
    equivalent), and last-known focused page inside each tracked context.

    **Public-ish fields**

    ``browser``, ``context``, ``page``
        Current active browser shell and—for this session—the active isolation
        context and top-level browsing target the library prefers for keywords
        that omit handles.

    **Internal fields** (omit from repr; maintained by methods)

    ``_contexts``
        Ordered list of context objects this session has explicitly registered via
        :meth:`_register_context`. This is **not** guaranteed to be every context
        the remote browser could ever enumerate; only what flowed through library
        calls that register context identities.

    ``_active_page_by_context``
        Maps ``id(context_python_object)`` to the most recently **bound** page for
        that context (tab). Used when switching context without creating a tab and
        when callers pass a concrete context handle rather than ``None``.

    ``_context_obj_ids`` / ``_context_str_ids``
        Fast membership mirrors of registered contexts—by Python ``id`` and by
        Vibium's ``context.id`` when present—for :meth:`resolve_context`.

    Typical construction is via :meth:`BrowserSession.create`, not bare ``cls(...)``.
    """

    browser: Any
    context: Any | None = None
    page: Any | None = None
    _contexts: list[Any] = field(default_factory=list, init=False, repr=False)
    _active_page_by_context: dict[int, Any] = field(
        default_factory=dict, init=False, repr=False
    )
    _context_obj_ids: set = field(default_factory=set, init=False, repr=False)
    _context_str_ids: set = field(default_factory=set, init=False, repr=False)

    @classmethod
    def create(
        cls,
        *,
        url: str | None = None,
        engine: str | None = None,
        channel: str | None = None,
        headless: bool = False,
        headers: dict[str, str] | None = None,
    ) -> BrowserSession:
        """Start one Vibium browser, wrap it in a ``BrowserSession``, bind default page."""
        from vibium import browser as vibium_browser

        browser = vibium_browser.start(
            url,
            engine=engine,
            channel=channel,
            headless=headless,
            headers=headers,
        )
        page = browser.page()
        session = cls(browser=browser, context=None, page=None)
        session._bind_active_page(page)
        return session

    def close(self) -> None:
        """Stop the browser subprocess and discard all tracked local state."""

        self.browser.stop()
        self._contexts.clear()
        self._active_page_by_context.clear()
        self._context_obj_ids.clear()
        self._context_str_ids.clear()
        self.context = None
        self.page = None

    def _bind_active_page(self, page: Any) -> None:
        """Register ``page``, its parent context, and mark both as globally active."""

        context = page.context
        self._register_context(context)
        self._active_page_by_context[id(context)] = page
        self.context = context
        self.page = page

    def require_page(self) -> Any:
        """Return ``self.page`` when set; raises ``BrowserSessionError`` otherwise."""

        if self.page is None:
            raise BrowserSessionError("No active page. Open a page first.")
        return self.page

    def get_active_context(self) -> Any:
        """Return the active :class:`~vibium.sync_api.context.BrowserContext` or raise."""

        if self.context is None:
            raise BrowserSessionError("No active context. Open context first.")
        return self.context

    def get_active_page_for_context(self, context: Any) -> Any:
        """Return the last bound page associated with ``context``, if any."""

        target = self.resolve_context(context=context)
        page = self._active_page_by_context.get(id(target))
        if page is None:
            raise BrowserSessionError(
                "No active page for provided context. Open a page first."
            )
        return page

    def resolve_context(self, context: Any | None = None) -> Any:
        """Resolve ``None`` as active context, or validate a handle belongs here."""

        if context is None:
            return self.get_active_context()
        if id(context) in self._context_obj_ids:
            return context
        ctx_id = getattr(context, "id", None)
        if ctx_id is not None and ctx_id in self._context_str_ids:
            return context
        raise BrowserSessionError(
            "Context handle is not associated with this browser session."
        )

    def set_active_page(self, page: Any) -> None:
        """Mark ``page`` (and its context) active; updates per-context memo map."""

        self._bind_active_page(page)

    def new_context(self) -> Any:
        """Create an isolated browser context via Vibium and make it active (no page yet)."""

        context = self.browser.new_context()
        self._register_context(context)
        self.context = context
        self.page = None
        return context

    def new_page(self, context: Any | None = None) -> Any:
        """Open a new tab inside ``context``, or inside the browser default stack when omitted."""

        if context is not None:
            target_context = self.resolve_context(context=context)
            page = target_context.new_page()
        else:
            page = self.browser.new_page()
        self._bind_active_page(page)
        return page

    def close_page(self, page: Any | None = None) -> None:
        """Resolve page to close, ask Vibium to close it, then repair active tab state."""

        target = self.require_page() if page is None else page
        target_context = target.context
        target.close()
        candidate = self._active_page_by_context.get(id(target_context))
        if candidate is target:
            candidate = None
        if candidate is None:
            for opened in self.browser.pages():
                if opened is target:
                    continue
                if getattr(opened.context, "id", None) == getattr(
                    target_context, "id", None
                ):
                    candidate = opened
                    break
        if candidate is not None:
            self._bind_active_page(candidate)
        else:
            self._active_page_by_context.pop(id(target_context), None)
            if self.context is target_context:
                self.page = None

    def contexts(self) -> list[Any]:
        """Return context objects registered on this session (library view, not full remote dump)."""

        return list(self._contexts)

    def pages(self) -> list[Any]:
        """Return all open pages according to Vibium (RPC); thin wrapper over ``browser.pages()``."""

        return list(self.browser.pages())

    def switch_context(self, context: Any) -> None:
        """Activate ``context`` and restore last remembered page for it (may be ``None``)."""

        target = self.resolve_context(context=context)
        self.context = target
        self.page = self._active_page_by_context.get(id(target))

    def close_context(self, context: Any | None = None) -> None:
        """Close a user context remotely and reconcile local bookkeeping."""

        target = self.resolve_context(context=context)
        target.close()
        if target in self._contexts:
            self._contexts.remove(target)
        self._context_obj_ids.discard(id(target))
        ctx_id = getattr(target, "id", None)
        if ctx_id is not None:
            self._context_str_ids.discard(ctx_id)
        self._active_page_by_context.pop(id(target), None)
        if self.context is target:
            self.context = self._contexts[-1] if self._contexts else None
            self.page = (
                self._active_page_by_context.get(id(self.context))
                if self.context
                else None
            )

    def _register_context(self, context: Any) -> None:
        """Append context to tracked list once and mirror ids into membership sets."""

        if context not in self._contexts:
            self._contexts.append(context)
        self._context_obj_ids.add(id(context))
        ctx_id = getattr(context, "id", None)
        if ctx_id is not None:
            self._context_str_ids.add(ctx_id)


@dataclass
class SessionPool:
    """Multi-browser facade used by ``Vibium`` library keywords.

    There is exactly one ``SessionPool`` instance per Robot library import; each
    :meth:`open` call appends another :class:`BrowserSession`.

    **Global active pointers** (Robot default scope)

        ``browser``, ``context``, ``page`` mirror the last session touched by most
        mutating APIs via :meth:`_sync_active_from_session`. Closing one browser via
        :meth:`close` promotes the chronologically **last remaining** browser in
        ``_sessions`` as the next global pointers.

    **Handle resolution**

        When keywords pass explicit ``browser=``, ``context=``, ``page=`` objects,
        lookups use ``id(handle)`` and—when meaningful—``.id`` from Vibium to find
        the owning :class:`BrowserSession` without scanning unrelated sessions.

        ``_purge_session_handles`` + ``_reindex_session`` rebuild that mapping whenever
        a session mutates locally so stale handles cannot point at the wrong
        ``BrowserSession`` after tab/context churn.

    **Internal fields**

        ``headless``, ``browser``, ``context``, ``page`` match constructor + global mirrors.
        ``_sessions`` is append-only-ish list of spawned :class:`BrowserSession`.
        Reverse maps (``_by_browser_id``, ``_by_context_id``, ``_by_context_str_id``,
        ``_by_page_id``, ``_by_page_str_id``) speed up ``_require_session_by_*``; they are fully
        rebuilt via :meth:`_reindex_session` after each coherent mutation burst.

    **Threading**

        Matches Vibium's sync client model: callers should invoke from the Robot
        test thread only.
    """

    headless: bool = False
    browser: Any | None = None
    context: Any | None = None
    page: Any | None = None
    _sessions: list[BrowserSession] = field(
        default_factory=list, init=False, repr=False
    )
    _by_browser_id: dict[int, BrowserSession] = field(
        default_factory=dict, init=False, repr=False
    )
    _by_context_id: dict[int, BrowserSession] = field(
        default_factory=dict, init=False, repr=False
    )
    _by_context_str_id: dict[Any, BrowserSession] = field(
        default_factory=dict, init=False, repr=False
    )
    _by_page_id: dict[int, BrowserSession] = field(
        default_factory=dict, init=False, repr=False
    )
    _by_page_str_id: dict[Any, BrowserSession] = field(
        default_factory=dict, init=False, repr=False
    )

    def open(
        self,
        *,
        url: str | None = None,
        engine: str | None = None,
        channel: str | None = None,
        headless: bool | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Create a new underlying :class:`BrowserSession` and return its browser handle."""
        launch_headless = self.headless if headless is None else headless

        session = BrowserSession.create(
            url=url,
            engine=engine,
            channel=channel,
            headless=launch_headless,
            headers=headers,
        )
        self._sessions.append(session)
        self._after_mutation(session)
        return session.browser

    def close(self, browser: Any | None = None) -> None:
        """Stop one browser; unregister it; promote globals to last remaining session."""

        if browser is None and self.browser is None:
            return
        target = self.resolve_browser(browser)
        session = self._require_session_by_browser(target)
        try:
            session.close()
        finally:
            # Keep pool indexes consistent even if browser.stop() fails.
            self._sessions = [s for s in self._sessions if s is not session]
            self._unindex_session(session, browser=target)
            self._activate_last_session(clear_when_empty=True)

    def close_all(self) -> None:
        """Best-effort shutdown of every tracked session; aggregates first wave of errors."""

        if not self._sessions:
            self._clear_globals()
            return

        failures: list[str] = []
        for session in list(self._sessions):
            try:
                session.close()
            except Exception as exc:  # pragma: no cover
                failures.append(str(exc))
        self._sessions.clear()
        self._by_browser_id.clear()
        self._by_context_id.clear()
        self._by_context_str_id.clear()
        self._by_page_id.clear()
        self._by_page_str_id.clear()
        self._clear_globals()
        if failures:
            raise BrowserSessionError(
                f"Unable to close one or more Browser sessions: {'; '.join(failures)}"
            )

    def require_page(self) -> Any:
        """Return the globally active ``page`` triple or raise."""

        if self.page is None:
            raise BrowserSessionError("No active page. Call `Open Browser` first.")
        return self.page

    def get_active_page(self, browser: Any | None = None) -> Any:
        """Global shortcut when ``browser`` omitted; scoped lookup when explicit handle given."""

        if browser is None:
            return self.require_page()
        session = self._require_session_by_browser(self.resolve_browser(browser))
        return session.require_page()

    def get_active_context(self, browser: Any | None = None) -> Any:
        """Always read through the owning :class:`BrowserSession` so globals stay truthful."""

        session = self._require_session_by_browser(self.resolve_browser(browser))
        return session.get_active_context()

    def get_active_page_for_context(self, context: Any) -> Any:
        """Forward to the ``BrowserSession`` that owns ``context``."""

        session = self._require_session_by_context(context)
        return session.get_active_page_for_context(context)

    def resolve_browser(self, browser: Any | None = None) -> Any:
        """Return active global browser when omitted; validate registration otherwise."""

        candidate = self.browser if browser is None else browser
        if candidate is None:
            raise BrowserSessionError("No active browser. Call `Open Browser` first.")
        if id(candidate) not in self._by_browser_id:
            raise BrowserSessionError(
                "Browser handle is not registered in this session."
            )
        return candidate

    def set_active_page(self, page: Any, browser: Any | None = None) -> None:
        """Focus bookkeeping for ``page``; optionally constrain to explicit ``browser``.

        Resolution prefers ``browser=`` when provided; otherwise uses reverse map
        of ``page`` to find owning session.
        """

        session = (
            self._require_session_by_browser(self.resolve_browser(browser))
            if browser is not None
            else self._require_session_by_page(page)
        )
        session.set_active_page(page)
        self._after_mutation(session)

    def pages(self, browser: Any | None = None) -> list[Any]:
        """Return open pages RPC list for resolved browser."""

        session = self._require_session_by_browser(self.resolve_browser(browser))
        return session.pages()

    def resolve_context(
        self, context: Any | None = None, browser: Any | None = None
    ) -> Any:
        """Resolve ``None`` -> active context; else validate membership + browser mismatch."""

        if context is None:
            return self.get_active_context(browser=browser)
        session = self._require_session_by_context(context)
        if browser is not None and session.browser is not self.resolve_browser(browser):
            raise BrowserSessionError(
                "Context handle does not belong to provided browser."
            )
        return session.resolve_context(context)

    def new_context(self, browser: Any | None = None) -> Any:
        """Create isolated browser context via pool-selected session."""

        def op(s: BrowserSession) -> Any:
            return s.new_context()

        return self._mutate_browser(browser, op)

    def new_page(self, context: Any | None = None, browser: Any | None = None) -> Any:
        """Create tab optionally bound to explicit ``context`` or default browser."""

        if context is not None:
            resolved = self.resolve_context(context=context, browser=browser)
            session = self._require_session_by_context(resolved)

            def op_with_context(s: BrowserSession) -> Any:
                return s.new_page(context=resolved)

            return self._mutate_session(session, op_with_context)
        session = self._require_session_by_browser(self.resolve_browser(browser))

        def op_default(s: BrowserSession) -> Any:
            return s.new_page()

        return self._mutate_session(session, op_default)

    def close_page(self, page: Any | None = None) -> None:
        """Delegate close to owning session identified by implicit active page or handle."""

        target = self.require_page() if page is None else page
        session = self._require_session_by_page(target)

        def op(s: BrowserSession) -> None:
            s.close_page(target)

        self._mutate_session(session, op)

    def contexts(self, browser: Any | None = None) -> list[Any]:
        """Return library-tracked contexts for chosen browser (not exhaustive remote enumeration)."""

        session = self._require_session_by_browser(self.resolve_browser(browser))
        return session.contexts()

    def switch_context(self, context: Any, browser: Any | None = None) -> None:
        """Update active context inside session and sync pool globals."""

        resolved = self.resolve_context(context=context, browser=browser)
        session = self._require_session_by_context(resolved)

        def op(s: BrowserSession) -> None:
            s.switch_context(resolved)

        self._mutate_session(session, op)

    def close_context(
        self, context: Any | None = None, browser: Any | None = None
    ) -> None:
        """Close remote user context plus local maps; then reconcile indices."""

        resolved = self.resolve_context(context=context, browser=browser)
        session = self._require_session_by_context(resolved)

        def op(s: BrowserSession) -> None:
            s.close_context(resolved)

        self._mutate_session(session, op)

    def browser_count(self) -> int:
        """Simple length of ``_sessions``; useful diagnostics for multi-browser setups."""

        return len(self._sessions)

    def resolve_scope(self, scope: Any | None = None) -> Any:
        """Keyword helper: implicit active ``page`` or explicit page/frame-like object unchanged."""

        return self.require_page() if scope is None else scope

    def _clear_globals(self) -> None:
        """Reset mirrored active triple stored on ``SessionPool`` itself."""

        self.browser = None
        self.context = None
        self.page = None

    def _after_mutation(self, session: BrowserSession) -> None:
        """Standard post-change hook: purge stale maps, rebuild, sync globals."""

        self._purge_session_handles(session)
        self._reindex_session(session)
        self._sync_active_from_session(session)

    def _mutate_session(
        self, session: BrowserSession, fn: Callable[[BrowserSession], Any]
    ) -> Any:
        """Invoke ``fn`` then always run ``_after_mutation``; return ``fn`` result."""

        result = fn(session)
        self._after_mutation(session)
        return result

    def _mutate_browser(
        self, browser: Any | None, fn: Callable[[BrowserSession], Any]
    ) -> Any:
        """``_mutate_session`` variant that first resolves owning session from browser handle."""

        session = self._require_session_by_browser(self.resolve_browser(browser))
        return self._mutate_session(session, fn)

    def _activate_last_session(self, clear_when_empty: bool = False) -> None:
        """After removals, optionally clear globals else copy trailing session."""

        if not self._sessions:
            if clear_when_empty:
                self._clear_globals()
            return
        self._sync_active_from_session(self._sessions[-1])

    def _sync_active_from_session(self, session: BrowserSession) -> None:
        """Copy ``browser``/``context``/``page`` references from mutated session outward."""

        self.browser = session.browser
        self.context = session.context
        self.page = session.page

    def _require_session_by_browser(self, browser: Any) -> BrowserSession:
        """Map python ``id(browser)`` to pooled session."""

        session = self._by_browser_id.get(id(browser))
        if session is None:
            raise BrowserSessionError(
                "Browser handle is not registered in this session."
            )
        return session

    def _require_session_by_context(self, context: Any) -> BrowserSession:
        """Resolve handle via `_by_context_id` / `_by_context_str_id` maps."""

        session = self._by_context_id.get(id(context))
        if session is not None:
            return session
        ctx_id = getattr(context, "id", None)
        if ctx_id is not None:
            session = self._by_context_str_id.get(ctx_id)
            if session is not None:
                return session
        raise BrowserSessionError(
            "Context handle is not associated with a registered browser in this session."
        )

    def _require_session_by_page(self, page: Any) -> BrowserSession:
        """Resolve handle via `_by_page_id` / `_by_page_str_id` maps."""

        session = self._by_page_id.get(id(page))
        if session is not None:
            return session
        page_id = getattr(page, "id", None)
        if page_id is not None:
            session = self._by_page_str_id.get(page_id)
            if session is not None:
                return session
        raise BrowserSessionError(
            "Page handle is not associated with a registered browser in this session."
        )

    def _purge_session_handles(self, session: BrowserSession) -> None:
        """Remove every reverse-map tuple pointing at ``session`` before rebuild."""

        for key in [k for k, v in self._by_context_id.items() if v is session]:
            self._by_context_id.pop(key, None)
        for key in [k for k, v in self._by_context_str_id.items() if v is session]:
            self._by_context_str_id.pop(key, None)
        for key in [k for k, v in self._by_page_id.items() if v is session]:
            self._by_page_id.pop(key, None)
        for key in [k for k, v in self._by_page_str_id.items() if v is session]:
            self._by_page_str_id.pop(key, None)

    def _reindex_session(self, session: BrowserSession) -> None:
        """Republish mappings for contexts/pages currently known on ``session``.

        Indexes both python object identity (`id(...)`) and Vibium's stable string ids
        when present so lookups survive wrapper recreation edge cases tied to `.id`.
        """

        self._by_browser_id[id(session.browser)] = session
        for context in session.contexts():
            self._by_context_id[id(context)] = session
            ctx_id = getattr(context, "id", None)
            if ctx_id is not None:
                self._by_context_str_id[ctx_id] = session
            tracked = session._active_page_by_context.get(id(context))
            if tracked is not None:
                self._by_page_id[id(tracked)] = session
                tid = getattr(tracked, "id", None)
                if tid is not None:
                    self._by_page_str_id[tid] = session
        if session.page is not None:
            self._by_page_id[id(session.page)] = session
            sid = getattr(session.page, "id", None)
            if sid is not None:
                self._by_page_str_id[sid] = session

    def _unindex_session(self, session: BrowserSession, *, browser: Any) -> None:
        """Detach entire browser closure from reverse maps upon session shutdown."""

        self._by_browser_id.pop(id(browser), None)
        self._purge_session_handles(session)
