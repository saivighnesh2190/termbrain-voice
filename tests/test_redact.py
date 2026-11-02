from termbrain_voice.redact import redact


def test_redacts_identifiers():
    raw = ("wlp2s0: link up 192.168.1.23 mac a4:c3:f0:11:22:33 uuid 123e4567-e89b-12d3-a456-426614174000 "
           "user vinn@example.com loopback 127.0.0.1")
    out = redact(raw, extra_secrets=["vinn-laptop"])
    assert "192.168.1.23" not in out and "<IP>" in out
    assert "a4:c3:f0" not in out and "<MAC>" in out
    assert "<UUID>" in out and "<EMAIL>" in out
    assert "127.0.0.1" in out


def test_redacts_hostname_and_user():
    out = redact("vinn-laptop NetworkManager[812]: device wlp2s0 vinn-laptop", extra_secrets=["vinn-laptop"])
    assert "vinn-laptop" not in out


def test_redacts_ssid():
    out = redact('NetworkManager: activating connection "KLU-Hostel-5G"')
    assert "KLU-Hostel" not in out
