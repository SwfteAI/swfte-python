# Voice Calls

List, fetch and audit calls placed against [Swfte Voice agents](https://www.swfte.com/products/voice).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# List recent calls (filter by status, channel, etc.)
recent = client.voice_calls.list(page=0, size=50, status="completed")
for call in recent.get("content", []):
    print(call["sid"], call["status"], call["durationSeconds"])

# Live calls
live = client.voice_calls.in_progress()
print(f"{len(live)} call(s) currently in progress")

# Get a single call
call_sid = "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # replace with your own
call = client.voice_calls.get(call_sid)

# Transcript
transcript = client.voice_calls.transcript(call_sid)
for turn in transcript["turns"]:
    print(f"[{turn['role']}] {turn['text']}")

# Recording metadata + URL
recording = client.voice_calls.recording(call_sid)
print(recording["url"], recording["durationSeconds"])

# Audit trail
audit = client.voice_calls.audit(call_sid)

# All calls placed against a specific chatflow
client.voice_calls.calls_for_chatflow("flow-onboarding", page=0, size=20)  # replace with your own
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
