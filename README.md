# Taskbar Lyrics

PCで再生中の曲の**同期歌詞を、Windowsのタスクバーの中に表示**する小さなツールです。
Spotify や ブラウザの YouTube など、Windowsのメディア再生情報に対応するアプリで動きます。

<img width="689" height="40" alt="image" src="https://github.com/user-attachments/assets/49ea10ad-d8de-479d-8f7b-cb3fec919aec" />


## 特徴

- **タスクバーの中に表示**：ジャケット画像・曲名・アーティスト名・歌詞を、クリックを邪魔しない透過ウィンドウで表示
- **音楽ではない動画は自動で非表示**：歌詞が見つからない動画（解説・実況など）では何も出しません
- **曲が切り替わっても消えない**：クロスフェードで滑らかに切り替え
- **5種類のデザイン**：Apple風 / Instagram風 / カラオケ風 / ネオン風 / ガラス風
- **次の歌詞の表示・文字サイズ・タイミング調整（±0.1〜0.5秒）**
- **全画面アプリ中は自動で隠す／一時停止中は薄くする**
- **位置合わせはタップで**：タスクバーを2回タップするだけ（タッチ操作の Surface 等でも快適）
- **省電力設計**：動かすときだけ30fpsで描画
- 自分の **.lrc ファイル** も使えます（歌詞が見つからない曲用）
- 設定は自動保存、Windows起動時の自動起動に対応

## 動作環境

- Windows 10 / 11（Surface Go 2 で動作確認しながら開発）
- Python 3.9〜3.12（EXEを使う場合は不要）

## インストール

### A. ソースから動かす
```bat
pip install -r requirements.txt
python taskbar_lyrics.py
```

### B. EXEを作る
`build_exe.bat` をダブルクリックすると、`dist\TaskbarLyrics.exe` ができます（Python 3.12 があれば自動で使います）。

## 使い方

1. 起動すると、タスクトレイ（時計の近く。`^` の中のこともあります）に赤い「♪」が出ます。
2. SpotifyやYouTubeで音楽を再生すると、歌詞が出ます（数秒かかることがあります）。
3. 「♪」をクリック／タップで設定メニューが開きます。
4. 最初に **「位置を合わせる」** で、歌詞を出したい範囲（アイコンの右〜時計の左）を2回タップしてください。

## 歌詞が出ないとき

- その曲が [LRCLIB](https://lrclib.net) に登録されていない可能性があります。
- 自分で用意した `.lrc` を `%APPDATA%\TaskbarLyrics\lyrics\` に置くと使われます（ファイル名に曲名を含めてください。例：`アーティスト - 曲名.lrc`）。メニューの「情報・歌詞データ」からフォルダを開けます。
- 動画の長さと歌詞の長さが大きく違うもの（長い前置き付きのMVなど）は、誤表示を避けるため出しません。
- 不具合報告には、メニューの「ログ・設定のフォルダ」にある `taskbar_lyrics.log` が役立ちます（曲名が含まれるので、貼る前に確認してください）。

## プライバシー

- 歌詞の検索のために、**曲名・アーティスト名・アルバム名・長さだけ**を LRCLIB（lrclib.net）に送ります。それ以外の情報は送りません。解析・広告・テレメトリはありません。
- 設定・ログ・歌詞キャッシュ・自作 `.lrc` は、すべて自分のPCの `%APPDATA%\TaskbarLyrics\` に保存されます。メニューの「歌詞キャッシュを削除」で消せます。
- LRCLIB への負荷を減らすため、見つからなかった曲は3日間は再検索せず、30秒未満・15分超の再生は検索しません。

## 免責

- 非公式のツールです。Spotify、Google/YouTube、Microsoft、LRCLIB とは関係ありません。
- 歌詞の著作権は各権利者に帰属します。本ツールは歌詞を同梱・再配布せず、利用者自身のPCに表示するだけです。スクリーンショットや動画を公開する際は、歌詞の写り込みにご配慮ください。
- 会社・学校の管理下のPCでは、ソフトの導入ルールに従ってください。
- 無保証です（MITライセンス）。

## ライセンス・クレジット

- 本ツールのコード：[MIT License](LICENSE)
- 歌詞データ：[LRCLIB](https://lrclib.net) 提供
- 使用ライブラリ：[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照（PySide6 は LGPL-3.0）

---

## English (short)

**Taskbar Lyrics** shows synced lyrics for the song you're playing (Spotify, YouTube in a browser, etc.) *inside* the Windows taskbar.
It reads the current track from the Windows media session (SMTC), fetches synced lyrics from [LRCLIB](https://lrclib.net), and hides itself for non-music videos.
Five visual styles, tap-to-calibrate placement, touch-friendly tray menu, low CPU use. Local `.lrc` files are supported.
Only track title / artist / album / duration are sent to LRCLIB. Unofficial; lyrics belong to their rights holders. MIT licensed.
Requires Windows 10/11 and Python 3.9–3.12 (`pip install -r requirements.txt`, then `python taskbar_lyrics.py`).
