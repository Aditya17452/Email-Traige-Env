"""Validator entrypoint module for multi-mode deployment checks."""

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run("environment:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
