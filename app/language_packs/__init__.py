from app.language_packs.base import LanguagePack
from app.language_packs.de import GermanPack
from app.language_packs.fr import FrenchPack
from app.language_packs.ja import JapanesePack


def get_language_pack(code: str) -> LanguagePack:
    code = code.lower().strip()
    mapping = {
        "de": GermanPack(),
        "fr": FrenchPack(),
        "ja": JapanesePack(),
    }
    if code not in mapping:
        raise ValueError(f"Unsupported language pack: {code}")
    return mapping[code]
