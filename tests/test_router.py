import json
from pathlib import Path

from termbrain_voice.router import route


def test_telugu_codemix_wifi():
    assert route("నా WiFi పని చేయడం లేదు")[0] == "network"


def test_telugu_script_only():
    assert route("బ్యాటరీ తొందరగా అయిపోతోంది")[0] == "power"


def test_zwnj_is_ignored():
    assert route("అప్\u200cడేట్ fail అయింది")[0] == "packages"


def test_no_substring_false_positive():
    # "plan" must not match "lan", "hotspot" must not match "hot"
    assert "network" not in route("I have a plan")
    assert route("hotspot not visible")[0] == "network"


def test_unknown_goes_general():
    assert route("hello there") == ["general"]


def test_router_eval_set_accuracy():
    cases = Path(__file__).resolve().parents[1] / "evals" / "router_cases.jsonl"
    rows = [json.loads(x) for x in cases.read_text(encoding="utf-8").splitlines() if x.strip()]
    hits = sum(route(r["text"])[0] == r["expect"] for r in rows)
    assert hits / len(rows) >= 0.9
