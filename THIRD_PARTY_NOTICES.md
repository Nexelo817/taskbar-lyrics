# Third-party notices

This project uses the following components. Each is distributed under its own license.

| Component | License | Notes |
|---|---|---|
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython/) | LGPL-3.0 (or GPL-3.0 / commercial) | UI. If you distribute a built EXE, the Qt libraries inside it remain under LGPL-3.0: keep this notice, and provide this project's source so users can rebuild/relink with a modified PySide6. |
| [winsdk](https://github.com/pywinrt/python-winsdk) | MIT | Access to Windows media session (SMTC) |
| [requests](https://github.com/psf/requests) | Apache-2.0 | HTTP client |
| [PyInstaller](https://pyinstaller.org/) (build only) | GPL-2.0 with bootloader exception | Used to build the EXE; the generated EXE is not GPL-restricted by it |

## Lyrics data

Synchronized lyrics are fetched at runtime from **[LRCLIB](https://lrclib.net)**.
Lyrics are the property of their respective rights holders. This project does not host or redistribute lyrics.
