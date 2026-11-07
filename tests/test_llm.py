from termbrain_voice.kb import Doc
from termbrain_voice.llm import ask_local_llm, build_prompt, parse_answer, speakable


def test_parse_fenced_json():
    raw = (
        'Sure!\n```json\n{"spoken_answer": "WiFi is off. Turn it on.", '
        '"steps": [{"command": "`rfkill list`", "why": "x"}], "confidence": "HIGH"}\n```'
    )
    a = parse_answer(raw)
    assert a["spoken_answer"] == "WiFi is off. Turn it on."
    assert a["steps"][0]["command"] == "rfkill list"
    assert a["confidence"] == "high"


def test_parse_garbage_falls_back():
    a = parse_answer("I think your wifi is off")
    assert a["confidence"] == "low" and "wifi" in a["spoken_answer"]


def test_speakable_strips_markdown_and_urls():
    out = speakable("**Run** `sudo rm x` now, see https://wiki.archlinux.org. Then # reboot")
    assert "`" not in out and "http" not in out and "*" not in out and "#" not in out


def test_prompt_has_language_rule_for_telugu():
    p = build_prompt("WiFi రావడం లేదు", "te-IN", "### Devices\nwlan0 unavailable", [Doc("wifi-down", "WiFi", ["network"], "body")])
    assert "Telugu script" in p and "[wifi-down]" in p and "wlan0 unavailable" in p


def test_ask_uses_json_mode_and_parses():
    seen = {}

    def fake_chat(**kw):
        seen.update(kw)
        return {"message": {"content": '{"spoken_answer": "ok", "steps": [], "sources": ["wifi-down"], "confidence": "medium"}'}}

    a = ask_local_llm("prompt", model="gemma3:4b", host="http://x", chat=fake_chat)
    assert seen["format"] == "json" and seen["model"] == "gemma3:4b"
    assert a["sources"] == ["wifi-down"]


def test_missing_model_message():
    import pytest

    def boom(**kw):
        raise Exception("model 'gemma3:4b' not found (status code: 404)")

    with pytest.raises(RuntimeError, match="ollama pull gemma3:4b"):
        ask_local_llm("p", model="gemma3:4b", host="http://x", chat=boom)


def test_local_ollama_ignores_proxy(monkeypatch):
    """httpx applies HTTP_PROXY to localhost; the local Ollama client must not."""
    import ollama

    from termbrain_voice import llm

    seen = {}

    class FakeClient:
        def __init__(self, host, **kw):
            seen["host"], seen["trust_env"] = host, kw.get("trust_env")

        def chat(self, **kw):
            return {"message": {"content": '{"answer": "ok", "steps": []}'}}

    monkeypatch.setattr(ollama, "Client", FakeClient)
    try:
        llm.ask_local_llm("hi", "gemma3:4b", "http://localhost:11434")
    except Exception:
        pass  # parsing details are covered elsewhere; we only check the client setup
    assert seen == {"host": "http://localhost:11434", "trust_env": False}
