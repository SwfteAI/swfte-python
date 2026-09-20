"""
Agent Mail V2 resource client — workspace mailboxes agents send from and
receive on.

Three things are load-bearing here, and all three are easy to get wrong:

1. **Inbound message content is untrusted external input.** Anyone who knows
   a mailbox address can put arbitrary bytes into it. ``subject``, ``text``,
   ``from``, ``to``, ``envelope_from`` and attachment metadata are *data,
   never instructions* — never splice them into an agent prompt, a shell
   command, a SQL string or an HTML page without isolating and escaping them.
2. **A send status of ``"accepted"`` is not delivery.** It means the upstream
   mail provider accepted the request. Bounces, spam filing and silent drops
   all happen afterwards and are not reflected in the send response.
3. **Agent binding requires a monolith deployment.** ``agent_id`` resolves
   against the agent registry that ships inside the monolith. On a standalone
   workspace-mail host, *any* ``agent_id`` — including a valid one — comes
   back as ``404 agent_not_found``.

Paging is opaque ``limit``/``cursor`` with ``nextCursor``: there is no page
number and no total page count.
"""

import re
from typing import Any, Dict, Optional

from ._base import V2Resource
from .exceptions import InvalidRequestError

#: Idempotency keys accepted by ``POST /v2/workspace-mail/mailboxes/{id}/messages``.
#: Validated client-side so a malformed key fails locally rather than burning a
#: send attempt.
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]{8,128}$")


class _Unset:
    """Sentinel meaning "caller did not supply this field"."""

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return "UNSET"

    def __bool__(self) -> bool:
        return False


#: Sentinel distinguishing "leave unchanged" from an explicit ``None``.
#: :py:meth:`AgentMail.update` needs the distinction because passing
#: ``agent_id=None`` is how you *clear* a binding.
UNSET = _Unset()


class AgentMail(V2Resource):
    """Client for ``/v2/workspace-mail``."""

    _path_prefix = "/v2/workspace-mail"

    # ---- status -------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """
        Report whether workspace mail is configured and usable.

        Answers ``501 setup_unavailable`` when the subsystem was never
        provisioned, and ``503 mail_unavailable`` when it is provisioned but
        the mail provider is down.
        """
        return self._request("GET", self._url("/status"))

    # ---- mailboxes ----------------------------------------------------

    def mailboxes(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List mailboxes.

        Paging is opaque: read ``nextCursor`` off the returned page and pass it
        back as ``cursor``. There is no page number and no total page count.

        Args:
            limit: Page size.
            cursor: Opaque cursor from a previous page's ``nextCursor``.
            agent_id: Only mailboxes bound to this agent.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if agent_id is not None:
            params["agentId"] = agent_id
        return self._request("GET", self._url("/mailboxes"), params=params)

    def get(self, mailbox_id: str) -> Dict[str, Any]:
        """Fetch one mailbox. ``404 mailbox_not_found`` when it does not exist."""
        return self._request("GET", self._url(f"/mailboxes/{mailbox_id}"))

    def create(
        self,
        name: str,
        local_part: str,
        agent_id: Optional[str] = None,
        domain_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a mailbox.

        ``409 mailbox_conflict`` when the local part is already taken on the
        domain. Supplying ``agent_id`` on a standalone host is
        ``404 agent_not_found`` regardless of whether the agent exists.

        Args:
            name: Human-readable label.
            local_part: Local part of the address. Immutable once created.
            agent_id: Agent to bind the mailbox to (monolith deployments only).
            domain_id: Custom mail domain to create the address under.
        """
        data: Dict[str, Any] = {"name": name, "localPart": local_part}
        if agent_id is not None:
            data["agentId"] = agent_id
        if domain_id is not None:
            data["domainId"] = domain_id
        return self._request("POST", self._url("/mailboxes"), data=data)

    def update(
        self,
        mailbox_id: str,
        name: Any = UNSET,
        agent_id: Any = UNSET,
    ) -> Dict[str, Any]:
        """
        Update a mailbox's name or agent binding.

        Fields left at :py:data:`UNSET` are omitted from the request and left
        alone. Pass ``agent_id=None`` **explicitly** to clear the binding — the
        sentinel exists precisely so that "don't touch it" and "unbind it" are
        different calls.

        ``local_part`` and ``address`` are immutable; the API answers
        ``400 invalid_request`` to any attempt to change them, which is why
        neither is exposed here.
        """
        data: Dict[str, Any] = {}
        if not isinstance(name, _Unset):
            data["name"] = name
        if not isinstance(agent_id, _Unset):
            data["agentId"] = agent_id
        return self._request("PATCH", self._url(f"/mailboxes/{mailbox_id}"), data=data)

    def remove(self, mailbox_id: str) -> Dict[str, Any]:
        """
        Deactivate a mailbox.

        This is **not** a destructive delete. The mailbox row and every message
        it holds stay readable; what stops is mail routing. The mailbox gains a
        ``deactivatedAt`` timestamp (``None`` means still active).

        Returns the deactivated mailbox when the server echoes it, or ``{}``
        when it answers ``204 No Content``.
        """
        return self._request("DELETE", self._url(f"/mailboxes/{mailbox_id}"))

    # ---- messages -----------------------------------------------------

    def messages(
        self,
        mailbox_id: str,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List messages in a mailbox.

        SECURITY: every returned message is untrusted external content. The
        subject, body, sender address and attachment filenames are chosen by
        whoever sent the mail. Treat them as data, never as instructions.

        Paging is opaque ``limit``/``cursor`` with ``nextCursor`` — not
        ``page``/``size``.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        return self._request(
            "GET",
            self._url(f"/mailboxes/{mailbox_id}/messages"),
            params=params,
        )

    def send(
        self,
        mailbox_id: str,
        to: str,
        subject: str,
        text: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """
        Send a message from a mailbox.

        This method **never retries**. A send is a side effect on the outside
        world, so a transparent retry could deliver the same mail twice. If you
        want a retry you must decide that yourself and reuse the *same*
        ``idempotency_key`` so the server can collapse the duplicate.

        ``idempotency_key`` is validated locally against
        ``^[a-zA-Z0-9._:-]{8,128}$`` **before any network call**; an invalid key
        raises :py:class:`~swfte.exceptions.InvalidRequestError` without
        contacting the API. Reusing a key with a *different* body is
        ``409 idempotency_conflict``.

        A successful response carries ``status: "accepted"``, which means the
        mail provider accepted the request — **not** that anything was
        delivered, and never that it was read.

        Args:
            mailbox_id: Mailbox to send from.
            to: Recipient address. Outside the allow-list this is
                ``403 recipient_not_allowed``.
            subject: Message subject.
            text: Plain-text body.
            idempotency_key: Stable key, 8-128 chars of ``[a-zA-Z0-9._:-]``.

        Raises:
            InvalidRequestError: If ``idempotency_key`` does not match the
                pattern. Raised locally; no request is made.
        """
        if not isinstance(idempotency_key, str) or not IDEMPOTENCY_KEY_PATTERN.match(
            idempotency_key
        ):
            raise InvalidRequestError(
                "Idempotency-Key must match ^[a-zA-Z0-9._:-]{8,128}$ "
                "(8-128 characters, letters, digits, dot, underscore, colon or "
                f"hyphen). Received: {idempotency_key!r}"
            )

        return self._request(
            "POST",
            self._url(f"/mailboxes/{mailbox_id}/messages"),
            data={"to": to, "subject": subject, "text": text},
            extra_headers={"Idempotency-Key": idempotency_key},
        )
