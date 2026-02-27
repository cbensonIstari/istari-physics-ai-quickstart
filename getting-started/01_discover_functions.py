"""Quickstart step: discover available Istari functions/tools."""

from __future__ import annotations

from istari_client import get_client, page_items


def safe_name(item: object, *names: str) -> str:
    for name in names:
        value = getattr(item, name, None)
        if value:
            return str(value)
    return "<unknown>"


def main() -> None:
    client = get_client()

    print("=== Functions (first 50) ===")
    functions_page = client.list_functions(size=50)
    functions = page_items(functions_page)
    for fn in functions:
        key = safe_name(fn, "key", "function", "name")
        display = safe_name(fn, "display_name", "name")
        print(f"- {key} :: {display}")

    print("\n=== Tools (first 50) ===")
    tools_page = client.list_tools(size=50)
    tools = page_items(tools_page)
    for tool in tools:
        key = safe_name(tool, "key", "name")
        display = safe_name(tool, "display_name", "name")
        print(f"- {key} :: {display}")


if __name__ == "__main__":
    main()
