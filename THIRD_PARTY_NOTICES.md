# Third-party notices

This project uses the following components. Each is distributed under its own license.

| Component | License | Notes |
|---|---|---|
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython/) | LGPL-3.0 (or GPL-3.0 / commercial) | UI. If you distribute a built EXE, the Qt libraries inside it remain under LGPL-3.0: keep this notice, and provide this project's source so users can rebuild/relink with a modified PySide6. |
| [winsdk](https://github.com/pywinrt/python-winsdk) | MIT | Access to Windows media session (SMTC) |
| [requests](https://github.com/psf/requests) | Apache-2.0 | HTTP client |
| [PyInstaller](https://pyinstaller.org/) (build only) | GPL-2.0 with bootloader exception | Used to build the EXE; the generated EXE is not GPL-restricted by it |

## Optional services

- **[LyricsPlus](https://lyricsplus.prjktla.my.id)**: an optional, off-by-default lyrics source. Used with the permission of the LyricsPlus team, in accordance with their terms of service and their attribution and caching requirements (lyrics are not stored on disk and are kept in memory for at most one hour).
- **[DeepL API](https://www.deepl.com/pro-api)**: used only when the user turns on translation with their own API key.

## Inspiration

- Feature ideas (lyric source display, word-level sync, lyric card, translation) were inspired by [YTM_Immersion](https://github.com/naikaku1/YTM_Immersion) (MIT License, Copyright (c) 2025 Naikaku). No code was copied.

## Lyrics data

Synchronized lyrics are fetched at runtime from **[LRCLIB](https://lrclib.net)**.
Lyrics are the property of their respective rights holders. This project does not host or redistribute lyrics.
