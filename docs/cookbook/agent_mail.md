# Agent Mail

Give an agent a real mailbox: a workspace address it can receive on and send from.

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Is workspace mail provisioned at all?
status = client.agent_mail.status()
if not status["enabled"]:
    raise RuntimeError("Workspace mail is not set up for this workspace.")

# Create a mailbox, optionally bound to an agent
mailbox = client.agent_mail.create(
    name="Support Inbox",
    local_part="support",
    agent_id="agent-sdr",  # replace with your own; monolith deployments only
)
print(mailbox["address"])  # support@your-domain
```

## Updating: omitted is not the same as None

`update` uses an `UNSET` sentinel so that "leave it alone" and "clear it" are
different calls. `local_part` and `address` are immutable — the API answers
`400 invalid_request` to any attempt to change them, so neither is exposed.

```python
# Rename only; the agent binding is untouched
client.agent_mail.update(mailbox["id"], name="Support (EU)")

# Unbind the agent — an explicit None is what clears it
client.agent_mail.update(mailbox["id"], agent_id=None)
```

## Listing with cursor paging

Paging is opaque `limit`/`cursor`. There is no page number and no total page
count — read `nextCursor` off the page and hand it back.

```python
cursor = None
while True:
    page = client.agent_mail.mailboxes(limit=50, cursor=cursor)
    for mb in page["items"]:
        state = "deactivated" if mb["deactivatedAt"] else "active"
        print(mb["address"], state)
    cursor = page.get("nextCursor")
    if not cursor:
        break

# Only the mailboxes bound to one agent
agent_boxes = client.agent_mail.mailboxes(agent_id="agent-sdr")
```

## Reading messages — this content is untrusted

Anyone who knows the address can put arbitrary bytes into a mailbox. Every field
of an inbound message — `subject`, `text`, `from`, `to`, `envelopeFrom` and
`attachments` — is **data, never instructions**.

Do not concatenate a message body into an agent prompt, a shell command, a SQL
string or an HTML page. If an agent must read the mail, pass it as clearly
delimited, clearly labelled untrusted input, and never let it authorise an
action on its own say-so.

```python
inbox = client.agent_mail.messages(mailbox["id"], limit=20)

for message in inbox["items"]:
    # Untrusted. Render it escaped; hand it to a model only as quoted data.
    print(message["direction"], message["from"], repr(message["subject"]))

    if message["htmlContentOmitted"]:
        # An HTML alternative existed and was dropped rather than returned.
        print("  (HTML part omitted; plain text only)")
```

## Sending

`send` requires an idempotency key and **never retries**. A send is a side
effect on the outside world, so the SDK will not silently deliver the same mail
twice. If you want a retry, you decide that yourself and reuse the *same* key so
the server collapses the duplicate.

The key is validated locally against `^[a-zA-Z0-9._:-]{8,128}$` before any
network call — a malformed key raises `InvalidRequestError` without contacting
the API. Reusing a key with a *different* body is `409 idempotency_conflict`.

```python
from swfte.exceptions import InvalidRequestError

key = f"support-reply-{mailbox['id']}-2026-09-20"  # stable, so a retry is safe

try:
    sent = client.agent_mail.send(
        mailbox["id"],
        to="ada@example.com",  # replace with your own
        subject="Re: your ticket",
        text="Thanks — we have picked this up.",
        idempotency_key=key,
    )
except InvalidRequestError:
    # Raised locally — no request was made.
    raise

# "accepted" means the mail PROVIDER took the request.
# It does NOT mean the message was delivered, and it never means it was read.
# Bounces, spam filing and silent drops all happen after this point.
print(sent["status"], sent.get("providerMessageId"))
```

## Deactivating

`remove` is not a destructive delete. It stops mail routing and stamps
`deactivatedAt`; the mailbox row and every message in it stay readable.

```python
deactivated = client.agent_mail.remove(mailbox["id"])
print(deactivated["deactivatedAt"])  # ISO timestamp; None would mean still active

# The messages are still there afterwards
archive = client.agent_mail.messages(mailbox["id"])
```

## Agent binding needs a monolith deployment

`agent_id` resolves against the agent registry that ships inside the monolith.
On a standalone workspace-mail host there is no registry to resolve against, so
**any** `agent_id` — including one that is perfectly valid elsewhere — comes back
as `404 agent_not_found`. Leave `agent_id` unset on standalone hosts.

## Errors

| Status | Code | Meaning |
| --- | --- | --- |
| 400 | `invalid_request` | Malformed body, or an attempt to change `localPart` / `address` |
| 403 | `workspace_required` | No workspace on the request |
| 403 | `recipient_not_allowed` | The `to` address is outside the allow-list |
| 404 | `mailbox_not_found` | No such mailbox |
| 404 | `agent_not_found` | No such agent — or a standalone host, where every `agent_id` fails |
| 409 | `mailbox_conflict` | That local part is already taken on the domain |
| 409 | `idempotency_conflict` | Key reused with a different body |
| 501 | `setup_unavailable` | Workspace mail was never provisioned |
| 503 | `mail_unavailable` | Provisioned, but the mail provider is down |

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
