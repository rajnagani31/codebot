import importlib
import os
import sys
import uvicorn


def run_server():
    # Ensure project root is on sys.path so `bot` package is importable
    _here = os.path.dirname(__file__)
    _repo_root = os.path.abspath(os.path.join(_here, ".."))
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

    try:
        importlib.import_module("bot.application.main")
        target = "bot.application.main:app"
    except ModuleNotFoundError:
        target = "main:app"

    uvicorn.run(target, host="localhost", port=8000, reload=True)


if __name__ == "__main__":
    run_server()
