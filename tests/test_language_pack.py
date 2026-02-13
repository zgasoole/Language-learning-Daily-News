from app.language_packs import get_language_pack


def test_german_pack_available() -> None:
    pack = get_language_pack("de")
    assert pack.code == "de"
    assert pack.default_voice()
