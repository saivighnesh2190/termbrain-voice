from termbrain_voice.kb import Retriever, error_lines, load_docs


def test_all_runbooks_load_with_ids():
    docs = load_docs()
    assert len(docs) >= 10
    assert len({d.id for d in docs}) == len(docs)
    assert all(d.topics for d in docs)


def test_retrieves_wifi_runbook():
    r = Retriever()
    top = r.search("WiFi not connecting soft blocked", topics=["network"], k=3)
    assert top[0].id == "wifi-down"


def test_error_lines_sharpen_query():
    r = Retriever()
    ev = "error: failed retrieving file 'ffmpeg' from mirror\nok line"
    top = r.search("update problem " + error_lines(ev), topics=["packages"], k=2)
    assert top[0].id == "failed-update"


def test_error_lines_filters():
    assert error_lines("all good\nError: x failed\nfine") == "Error: x failed"
