from __future__ import annotations

import sys
import sysconfig
from pathlib import Path


_installed_werkzeug = Path(sysconfig.get_paths()["purelib"]) / "werkzeug"
if _installed_werkzeug.exists():
    installed_path = str(_installed_werkzeug)
    if installed_path not in __path__:
        __path__.append(installed_path)
    _installed_init = _installed_werkzeug / "__init__.py"
    if _installed_init.exists():
        exec(compile(_installed_init.read_text(), str(_installed_init), "exec"), globals())
