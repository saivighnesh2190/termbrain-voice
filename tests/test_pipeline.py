from termbrain_voice.config import Settings
from termbrain_voice.gnani import OfflineGnani
from termbrain_voice.pipeline import run

FAKE_OUTPUT = {
    ("rfkill", "list"): "0: phy0: Wireless LAN\n\tSoft blocked: yes\n\tHard blocked: no",
    ("nmcli",): "wlp2s0:wifi:unavailable:\nlo:loopback:connected (externally):lo",
}


def fake_runner(argv):
    for key, out in FAKE_OUTPUT.items():
        if tuple(argv[: len(key)]) == key:
            return out
    return "(no output)"


def fake_chat(**kw):
    prompt = kw["messages"][1]["content"]
    assert "Soft blocked: yes" in prompt  # evidence reached the local model
    assert "Telugu script" in prompt
    return {"message": {"content": (
        '{"spoken_answer": "మీ WiFi software లో off అయి ఉంది. rfkill తో unblock చేయండి.",'
        '"diagnosis": "WiFi is soft-blocked.", "likely_cause": "rfkill soft block",'
        '"steps": [{"command": "rfkill list", "why": "confirm"},'
        '{"command": "rfkill unblock wifi", "why": "turn radio on"},'
        '{"command": "sudo rm -rf /etc/NetworkManager", "why": "reset"}],'
        '"sources": ["wifi-down", "made-up-id"], "confidence": "high"}'
    )}}


def test_end_to_end_offline(tmp_path):
    settings = Settings(gnani_api_key="", data_dir=tmp_path)
    wav = tmp_path / "q.wav"
    wav.write_bytes(b"RIFF")
    speech = OfflineGnani("నా WiFi పని చేయడం లేదు", "te-IN")
    s = run(settings, speech, audio_path=wav, runner=fake_runner, chat=fake_chat)
    assert s.topics[0] == "network"
    assert s.reply_language == "te-IN"
    assert "wifi-down" in s.sources_retrieved
    assert s.answer["sources"] == ["wifi-down"]  # invented citation dropped
    assert [st["safety"] for st in s.steps] == ["read-only", "changes system"]
    assert len(s.blocked_steps) == 1  # rm -rf withheld
    assert s.spoken_audio.endswith(".wav")
    assert set(s.sent_to_cloud) == {"stt", "tts"}
    assert "Soft blocked" not in s.sent_to_cloud["tts"]  # evidence never goes to the cloud
    assert s.save(tmp_path).exists()


def test_text_mode_skips_stt(tmp_path):
    settings = Settings(gnani_api_key="", data_dir=tmp_path)
    s = run(settings, OfflineGnani(), text="no space left on device", speak=False,
            runner=lambda argv: "(no output)",
            chat=lambda **kw: {"message": {"content": '{"spoken_answer": "Disk is full.", "steps": []}'}})
    assert s.topics[0] == "disk" and "stt" not in s.sent_to_cloud and not s.spoken_audio
