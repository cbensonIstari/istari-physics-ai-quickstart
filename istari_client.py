"""Shared Istari client helper for quickstart scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable

from dotenv import load_dotenv
from istari_digital_client import Client, Configuration


@dataclass(frozen=True)
class IstariSettings:
    registry_url: str
    auth_token: str


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def load_settings() -> IstariSettings:
    load_dotenv()
    return IstariSettings(
        registry_url=_require_env("ISTARI_DIGITAL_REGISTRY_URL"),
        auth_token=_require_env("ISTARI_DIGITAL_REGISTRY_AUTH_TOKEN"),
    )


def get_client() -> Client:
    settings = load_settings()
    config = Configuration(
        registry_url=settings.registry_url,
        registry_auth_token=settings.auth_token,
    )
    return Client(config)


def page_items(page_like: Any) -> list[Any]:
    """Normalize SDK pagination responses across versions."""
    if page_like is None:
        return []
    if isinstance(page_like, list):
        return page_like
    items = getattr(page_like, "items", None)
    if items is not None:
        return list(items)
    content = getattr(page_like, "content", None)
    if content is not None:
        return list(content)
    if isinstance(page_like, Iterable):
        return list(page_like)
    return [page_like]


def _field(obj: Any, name: str, default: str = "") -> str:
    value = getattr(obj, name, default)
    return str(value) if value is not None else default


def print_connection_summary() -> None:
    client = get_client()
    user = client.get_current_user()
    email = _field(user, "email", "<unknown-email>")
    full_name = _field(user, "name", "<unknown-name>")
    print(f"Connected as: {full_name} ({email})")


if __name__ == "__main__":
    print_connection_summary()
