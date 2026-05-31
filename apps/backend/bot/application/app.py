import importlib
import os
import sys
import uvicorn


def run_server():
    # Ensure project root is on sys.path for apps.backend package
    _here = os.path.dirname(__file__)
    _repo_root = os.path.abspath(os.path.join(_here, "../../../../"))
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

    try:
        importlib.import_module("apps.backend.bot.application.main")
        target = "apps.backend.bot.application.main:app"
    except ModuleNotFoundError:
        target = "main:app"

    uvicorn.run(target, host="localhost", port=8001, reload=True)


if __name__ == "__main__":
    run_server()
