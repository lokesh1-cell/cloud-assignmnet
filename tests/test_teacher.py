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


def test_evaluation_retries_transport_errors_without_altering_reply(monkeypatch):
    import urllib.error
    import eval_teacher

    raw = ' \n{"intent":"alarm_set","date":null,"time":"eight am","place":null}\n '
    replies = iter([urllib.error.URLError("transient transport failure"), raw])

    def call(*args):
        value = next(replies)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(eval_teacher.label_worker, "call_teacher", call)
    monkeypatch.setattr(eval_teacher.time, "sleep", lambda seconds: None)
    assert eval_teacher.get_prediction("{{COMMAND}}", "wake me up at eight am") == raw
