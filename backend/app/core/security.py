# backend/app/core/security.py
import hashlib
import json
from typing import Any


def compute_request_hash(payload: dict[str, Any]) -> str:
    normalized_json = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()
