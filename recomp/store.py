"""Encrypted storage. Everything committed to the repo is encrypted with DATA_KEY,
so the repo can be public without exposing health data or Garmin tokens."""
import json, os
from cryptography.fernet import Fernet


def _fernet():
    key = os.environ.get("DATA_KEY")
    if not key:
        raise SystemExit("DATA_KEY is not set. Add it as a GitHub secret (or export it locally).")
    return Fernet(key.encode())


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "rb") as f:
        return json.loads(_fernet().decrypt(f.read()))


def save_json(path, obj):
    with open(path, "wb") as f:
        f.write(_fernet().encrypt(json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()))


def load_text(path):
    with open(path, "rb") as f:
        return _fernet().decrypt(f.read()).decode()


def save_text(path, text):
    with open(path, "wb") as f:
        f.write(_fernet().encrypt(text.encode()))
