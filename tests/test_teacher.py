"""The generated teacher string must reach storage without whitespace edits."""

import io
import json

import label_worker


def test_teacher_response_preserves_exact_whitespace(monkeypatch):
    raw = ' \n{"intent":"datetime_query","date":null,"time":null,"place":null}\n '
    payload = json.dumps({"response": raw}).encode()
    monkeypatch.setattr(
        label_worker.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(payload)
    )
    assert label_worker.call_teacher("{{COMMAND}}", "what time is it") == raw
