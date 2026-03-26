from pathlib import Path


_backend_bot_path = Path(__file__).resolve().parent.parent / "backend" / "bot"
__path__ = [str(_backend_bot_path)]
