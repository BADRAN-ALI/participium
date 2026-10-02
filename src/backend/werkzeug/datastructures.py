from __future__ import annotations

import sysconfig
from pathlib import Path


_real_package_path = Path(sysconfig.get_paths()["purelib"]) / "werkzeug" / "datastructures"
_real_init_path = _real_package_path / "__init__.py"

if _real_init_path.exists():
    __path__ = [str(_real_package_path)]
    __package__ = __name__
    exec(compile(_real_init_path.read_text(), str(_real_init_path), "exec"), globals())
else:
    from dataclasses import dataclass

    @dataclass
    class FileStorage:
        filename: str | None = None
        content_type: str | None = None
