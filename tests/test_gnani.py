import json

import pytest

from termbrain_voice.config import Settings
from termbrain_voice.gnani import GnaniClient, GnaniError


class FakeResp:
    def __init__(self, status, body=None, content=b""):
        self.status_code = status
        self._body = body
        self.content = content
        self.text = json.dumps(body) if body is not None else ""
        self.reason = "x"

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def post(self, url, timeout=None, **kw):
        self.calls.append((url, kw))
        return self.responses.pop(0)


def settings():
    return Settings(gnani_api_key="test-key", gnani_base_url="https://api.vachana.ai")


def test_transcribe_sends_prisma_v3_codemix_and_keyterms(tmp_path):
    wav = tmp_path / "q.wav"
    wav.write_bytes(b"RIFF....")
    sess = FakeSession([FakeResp(200, {"success": True, "transcript": "నా WiFi పని చేయడం లేదు",
                                       "detected_language_code": "te-IN", "request_id": "r1"})])
    tr = GnaniClient(settings(), session=sess).transcribe(wav)
    url, kw = sess.calls[0]
    assert url == "https://api.vachana.ai/stt/v3"
    assert kw["data"]["model"] == "prisma-v3.0"
    assert kw["data"]["format"] == "codemix"
    assert kw["data"]["language_code"] == "te-IN,en-IN"
    assert "pacman" in json.loads(kw["data"]["keyterms"])
    assert sess.headers["X-API-Key-ID"] == "test-key"
    assert tr.language == "te-IN" and "WiFi" in tr.text


def test_tts_payload_and_bytes(tmp_path):
    sess = FakeSession([FakeResp(200, None, content=b"RIFFwav")])
    out = GnaniClient(settings(), session=sess).synthesize("WiFi off ఉంది", "te-IN", tmp_path / "r.wav")
    url, kw = sess.calls[0]
    assert url.endswith("/api/v1/tts/inference")
    assert kw["json"]["model"] == "timbre-v3.0" and kw["json"]["language"] == "te-IN"
    assert out.read_bytes() == b"RIFFwav"


def test_rate_limit_retries_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr("termbrain_voice.gnani.time.sleep", lambda s: None)
    wav = tmp_path / "q.wav"
    wav.write_bytes(b"x")
    rl = FakeResp(429, {"detail": {"error_code": "RATE_LIMITED", "message": "1 active", "status_code": 429}})
    ok = FakeResp(200, {"success": True, "transcript": "hello", "detected_language_code": "en-IN"})
    sess = FakeSession([rl, ok])
    assert GnaniClient(settings(), session=sess).transcribe(wav).text == "hello"
    assert len(sess.calls) == 2


@pytest.mark.parametrize("status,body,code", [
    (400, {"success": False, "error": {"type": "MAX_AUDIO_DURATION_EXCEEDED", "message": "30 s"}}, "MAX_AUDIO_DURATION_EXCEEDED"),
    (401, {"detail": {"error_code": "INVALID_API_KEY", "message": "Unauthorized"}}, "INVALID_API_KEY"),
    (422, {"detail": [{"loc": ["body", "language_code"]}]}, "VALIDATION_ERROR"),
])
def test_error_shapes(tmp_path, status, body, code):
    wav = tmp_path / "q.wav"
    wav.write_bytes(b"x")
    sess = FakeSession([FakeResp(status, body)])
    with pytest.raises(GnaniError) as ei:
        GnaniClient(settings(), session=sess).transcribe(wav)
    assert ei.value.code == code


def test_missing_key_is_clear():
    with pytest.raises(GnaniError):
        GnaniClient(Settings(gnani_api_key=""))
