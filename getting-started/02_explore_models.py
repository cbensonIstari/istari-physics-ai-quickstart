"""Quickstart step: list recently available models/files for manual selection."""

from __future__ import annotations

from istari_client import get_client, page_items


def describe(item: object) -> tuple[str, str]:
    item_id = str(getattr(item, "id", "<no-id>"))
    name = getattr(item, "display_name", None) or getattr(item, "name", None) or "<unnamed>"
    return item_id, str(name)


def main() -> None:
    client = get_client()

    # Different tenants may expose model listings via different endpoints.
    # We try the common one and provide clear fallback guidance.
    if not hasattr(client, "list_models"):
        print("This SDK version does not expose client.list_models().")
        print("Use Istari UI to grab model IDs for geometry inputs and campaign root model.")
        return

    page = client.list_models(size=25)
    models = page_items(page)
    print("=== Models (first 25) ===")
    for model in models:
        model_id, name = describe(model)
        print(f"- {model_id} :: {name}")


if __name__ == "__main__":
    main()
