# プライバシー / Privacy

**最終更新：2026年10月21日**

Taskbar Lyrics は、利用者の個人情報を収集しません。解析・広告・テレメトリ（利用状況の送信）はありません。
この文書は、何をPCに保存して、何を外部に送るのか、そして、利用者が何を決められるのかを説明します。

## 1. 集める情報

### A. 手元のPCに保存するもの
すべて `%APPDATA%\TaskbarLyrics\` の中です。

| ファイル | 内容 |
|---|---|
| `settings.json` | 設定（デザイン、位置など）。翻訳を使う場合は、DeepL APIキーも含みます。**他の人に渡さないでください** |
| `cache.json` | 見つかった歌詞と、見つからなかった曲の記録（上限400件） |
| `translations.json` | 保存してある翻訳（翻訳をオンにしたとき。上限300曲） |
| `offsets.json` | 曲ごとのタイミング調整 |
| `taskbar_lyrics.log` | 動作のログ（再生した曲名が含まれます） |
| `lyrics\` | 利用者が置いた .lrc ファイル |

「Windows起動時に自動起動」をオンにしたときだけ、ユーザーのスタートアップ設定（レジストリの `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`）に、1件追加します。オフにすると、削除されます。

### B. 外部に送るもの

**歌詞の検索（LRCLIB）**
- 送り先：[LRCLIB](https://lrclib.net)（lrclib.net）
- 送るもの：再生中の曲の**曲名・アーティスト名・アルバム名・曲の長さ**。アプリ名とバージョン（User-Agent。例：`TaskbarLyrics/2.2.0`）。通信の性質上、お使いのPCのIPアドレスが、LRCLIB側に届きます
- 目的：タイムスタンプ付きの歌詞を探すため
- メモ：30秒未満・15分超の再生は検索しません。見つからなかった曲は、3日間は再検索しません
- **止める方法**：メニューの「歌詞の取得元」で、LRCLIB をオフにします。オフの間は、何も送りません（自分の .lrc と、保存した歌詞だけを使います）

**歌詞の検索（LyricsPlus）：オンにしたときだけ・LRCLIBで見つからない曲だけ**
- 送り先：[LyricsPlus](https://lyricsplus.prjktla.my.id)（`lyricsplus.prjktla.my.id`）。運営チームから、このツールへの組み込みの許可をもらっています
- 送るもの：**曲名・アーティスト名・アルバム名・曲の長さ**。アプリ名とバージョン（User-Agent）。IPアドレスが届くことは、LRCLIBと同じです
- 目的：LRCLIBに無い曲の、（単語ごとの時刻つきの）歌詞を探すため
- メモ：1曲あたり、最大2回まで。返ってきた歌詞は、**ディスクに保存せず**、メモリの中でも、1時間までしか使い回しません。「見つからなかった」も、ディスクに記憶しません。最初にオンにするときに、確認の画面が出ます
- **止める方法**：メニューの「歌詞の取得元」で、LyricsPlus をオフにします（標準はオフです）
- LyricsPlus側の情報の扱いと、利用規約は、LyricsPlus のサイトを確認してください

**翻訳（DeepL）：オンにしたときだけ**
- 送り先：DeepL（`api-free.deepl.com` または `api.deepl.com`）
- 送るもの：その曲の**歌詞の文章**。あなた自身の DeepL APIキーを使います
- 目的：歌詞の日本語訳を、表示するため
- メモ：曲ごとに1回だけ送って、結果はPCに保存します。最初にオンにするときに、確認の画面が出ます。日本語の歌詞は、送りません
- **止める方法**：メニューの「翻訳（DeepL）」で、オフにします。「APIキーを削除」で、保存したキーも消せます
- DeepL側の情報の扱いは、DeepL のサイトを確認してください

**送らないもの**
- ジャケット画像は、Windowsの再生情報から手元で読み取るだけで、どこにも送りません
- 「歌詞カード」の画像は、手元のPCで作るだけで、どこにも送りません。コピーや保存をするのは、利用者自身です
- 設定、ログ、再生履歴、ログイン情報、パスワードは、送りません。このツールは、それらを扱いません

## 2. 情報の使いみち
- 歌詞と翻訳を、タスクバーに表示するため
- 曲ごとのタイミング調整や、設定を、覚えておくため
- 一度見つけた歌詞を、使い回して、通信を減らすため

## 3. 共有・開示
**利用者の情報を、販売したり、交換したり、ほかの人に渡したりしません。**
外部への送信は、上の「B. 外部に送るもの」の、歌詞を表示するための通信だけです。

## 4. 利用者が決められること

| やりたいこと | 方法 |
|---|---|
| LRCLIBへの送信を止める | メニュー「歌詞の取得元」で LRCLIB をオフ |
| LyricsPlusへの送信を止める | メニュー「歌詞の取得元」で LyricsPlus をオフ（標準はオフ） |
| 翻訳（DeepLへの送信）を止める | メニュー「翻訳（DeepL）」でオフ。APIキーは「APIキーを削除」 |
| 保存した歌詞と翻訳を消す | メニュー「情報・歌詞データ」→「歌詞キャッシュを削除」 |
| すべての保存データを消す | `%APPDATA%\TaskbarLyrics\` フォルダごと削除 |
| 自動起動をやめる | メニュー「Windows起動時に自動起動」をオフ |
| ログの内容を細かくする・戻す | メニュー「情報・歌詞データ」→「詳細ログ」 |

### ログについて
不具合を報告するとき、ログには再生した曲名が含まれます。メニューの「詳細ログ」をオンにすると、検索に使った文字列（曲名・アーティスト名）も残ります。公開の場所に貼る前に、内容を確認してください。

## 5. この文書の変更
変更したときは、この文書を更新して、「最終更新」の日付を書き換えます。

---

## English (short)
Taskbar Lyrics collects no personal data and has no analytics or ads.
- **Lyrics lookup (LRCLIB)**: sends the track title, artist, album and duration (plus an app-name/version User-Agent; your IP address reaches the server, as with any request). You can turn this off in the tray menu ("歌詞の取得元" → LRCLIB); the app then uses only your own `.lrc` files and the lyrics saved on your PC.
- **Lyrics lookup (LyricsPlus), opt-in and off by default**: only if you turn it on, and only for tracks LRCLIB doesn't have, the same track metadata is sent to LyricsPlus (used with the LyricsPlus team's permission). The returned lyrics are never stored on disk and are kept in memory for at most one hour; misses are not remembered on disk.
- **Translation (DeepL), opt-in**: only if you turn it on with your own API key, the lyrics text of the current song is sent once to DeepL; the result is cached locally. Your key is stored in `settings.json`.
- Cover art is read locally from Windows and is never sent. Lyric-card images are made locally and never uploaded.
- Settings, a lyrics cache, saved translations, per-song offsets, a log (which contains track titles) and your own `.lrc` files are stored in `%APPDATA%\TaskbarLyrics\`. Delete that folder to remove everything.
- If you enable autostart, one entry is added to your user's Run registry key, and it is removed when you turn it off.
