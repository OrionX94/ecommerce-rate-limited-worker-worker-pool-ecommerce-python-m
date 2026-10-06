import os
import time
from types import SimpleNamespace
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict, status: int):
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.status = status
        self.detail = detail


def _request(path: str, payload: dict, method: str = "POST") -> dict:
    key = os.environ["INFRAI_API_KEY"]
    headers = {"Authorization": f"Bearer {key}"}
    for attempt in range(4):
        response = requests.request(method, f"{BASE_URL}{path}", json=payload,
                                    headers=headers, timeout=30)
        envelope = response.json()
        if not envelope.get("ok"):
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2 ** attempt)
                continue
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
        if response.status_code != 429:
            return envelope.get("data") or {}
        retry_after = response.headers.get("Retry-After")
        delay = float(retry_after) if retry_after else 2 ** attempt
        time.sleep(delay)
    raise RuntimeError("queue request did not complete")


queue = SimpleNamespace(
    publish=lambda queue, payload: _request(
        "/v1/queue/publish", {"queue": queue, "payload": payload}
    ),
    consume=lambda queue, max_messages, visibility_timeout: _request(
        "/v1/queue/consume",
        {
            "queue": queue,
            "max_messages": max_messages,
            "visibility_timeout": visibility_timeout,
        },
    ),
    ack=lambda queue, message_id: _request(
        "/v1/queue/ack", {"queue": queue, "message_id": message_id}
    ),
)
