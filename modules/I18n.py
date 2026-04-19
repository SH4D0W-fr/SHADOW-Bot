import json
import logging
from pathlib import Path
from typing import Any

from config import Config


_locale_data: dict[str, Any] = {}
_active_language = "fr"


def _locales_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "locales"


def _read_locale_file(language: str) -> dict[str, Any]:
    locale_file = _locales_dir() / f"{language}.json"
    if not locale_file.exists():
        return {}

    try:
        with locale_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as e:
        logging.error("Erreur chargement locale %s: %s", language, str(e))

    return {}


def load_locale(language: str | None = None) -> str:
    global _locale_data, _active_language

    target_language = (language or getattr(Config, "Language", "fr") or "fr").lower()

    data = _read_locale_file(target_language)
    if not data:
        logging.warning("Locale %s introuvable, fallback sur fr", target_language)
        target_language = "fr"
        data = _read_locale_file("fr")

    if not data:
        logging.error("Aucune locale chargée depuis locales/")
        _locale_data = {}
        _active_language = target_language
        return _active_language

    _locale_data = data
    _active_language = target_language
    logging.info("Locale active: %s", _active_language)
    return _active_language


def get_language() -> str:
    return _active_language


def _resolve_key(data: dict[str, Any], key: str) -> Any:
    current: Any = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def t(key: str, default: str | None = None, **kwargs: Any) -> str:
    value = _resolve_key(_locale_data, key)

    if value is None:
        fallback_fr = _resolve_key(_read_locale_file("fr"), key)
        if fallback_fr is not None:
            value = fallback_fr

    if value is None:
        value = default if default is not None else key

    if not isinstance(value, str):
        value = str(value)

    if kwargs:
        try:
            value = value.format(**kwargs)
        except Exception:
            pass

    return value


# Chargement initial à l'import selon Config.Language
load_locale(getattr(Config, "Language", "fr"))
