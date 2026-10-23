# Taskbar Lyrics

![License: MIT](https://img.shields.io/badge/license-MIT-blue) ![Platform: Windows 10/11](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4) ![Python 3.9-3.12](https://img.shields.io/badge/python-3.9--3.12-3776ab)

PCで再生中の曲の**同期歌詞を、Windowsのタスクバーの中に表示**する小さなツールです。
Spotify や ブラウザの YouTube など、Windowsの「再生中」情報に対応するアプリで、そのまま動きます。

![Taskbar Lyrics](docs/header.png)

> 画像の歌詞とジャケットは、サンプルです。

> **現在は、ベータ版（v2.3.1-beta.1）です。** 安定版（v1.2）に、歌詞カード・翻訳・単語同期・取得元の表示などを足した版で、不具合があるかもしれません。
> ベータ版は、[Releases の一覧](https://github.com/Nexelo817/taskbar-lyrics/releases) の、「Pre-release」と書かれたものです。見つけた不具合は、[Issues](https://github.com/Nexelo817/taskbar-lyrics/issues) で教えてください。

## 特徴

- **タスクバーの中に表示**：ジャケット画像・曲名・アーティスト名・歌詞を、クリックを邪魔しない透過ウィンドウで表示します。後ろのウィンドウは、普通に操作できます
- **曲が変わっても消えない**：次の曲の歌詞を探している間も表示を残し、見つかった時点でクロスフェードで切り替えます。曲の切れ目で再生情報が一瞬途切れても、0.9秒は消しません
- **音楽ではない動画は自動で非表示**：歌詞が見つからない動画（解説・実況など）では何も出しません。曲の長さと曲名も確かめます
- **いま、どこから取った歌詞かが分かる**：メニューの先頭に、「LRCLIB（曲名で検索）／行同期」のように、取得元と同期の細かさを表示します
- **単語ごとの同期**：単語の時刻つきの `.lrc`（拡張LRC）を置くと、カラオケ風で、歌う単語に合わせて色が流れます
- **歌詞カード**：歌詞から1〜4行を選んで、ジャケットの色の画像にして、コピーか保存ができます。画像は手元で作るだけで、どこにも送信しません
- **5種類のデザイン**：Apple風 / Instagram風 / カラオケ風 / ネオン風 / ガラス風
- **位置合わせはタップで**：タスクバーを2回タップするだけで、歌詞を出す範囲を決められます。タッチ操作の端末（Surface Go 2 など）でも迷いません
- **YouTubeのタイトルに強い**：「アーティスト - 曲名」「【MV】曲名 / アーティスト」のような形から曲名とアーティストを推測し、表記ゆれにも対応します
- **取得元のオン・オフ**：LRCLIB への送信を、メニューから止められます。止めている間は、通信せずに、自分の .lrc と保存した歌詞だけを使います
- **LyricsPlus（任意・標準はオフ）**：オンにすると、LRCLIBで見つからない曲だけ、[LyricsPlus](https://lyricsplus.prjktla.my.id) から歌詞を探します（単語ごとの同期があれば、カラオケ風で単語に合わせて色が流れます）。運営チームから、このツールへの組み込みの許可をもらっています
- **歌詞の翻訳（DeepL）**：オンにすると、歌詞の下に日本語訳を小さく表示します。あなた自身の DeepL APIキーが必要です（歌詞の文章を DeepL に送ります）
- **曲ごとのタイミング調整**：ズレて見える曲だけ、0.1秒単位で早めたり遅らせたりして、その曲用に保存できます（全曲まとめての調整も可能）
- **次の歌詞・文字サイズ**：次の歌詞を小さく出す二行表示、文字サイズ（小・標準・大）
- **自分の .lrc ファイルも使えます**：歌詞が見つからない曲用です
- **省電力設計**：アニメーションは動かすときだけ30fpsで描画します
- **そのほか**：全画面アプリ中は自動で隠す／一時停止中は薄くする／Windows起動時の自動起動／現在の歌詞をコピー／設定の自動保存／二重起動の防止／詳細ログ（不具合調査用）

## 対応環境

- Windows 10 / 11（Surface Go 2 で動作確認しながら開発しています）
- ソースから動かす場合は Python 3.9〜3.12（`winsdk` が 3.13 以降に未対応のため）
- Mac / Linux には、現在は対応していません

## インストール

### A. EXEで使う（おすすめ・インストール不要）
1. [Releases](https://github.com/Nexelo817/taskbar-lyrics/releases) から `TaskbarLyrics.exe` をダウンロードします（新機能を使うには、「Pre-release」のベータ版を選びます。「Latest」は、安定版 v1.2 です）
2. ダブルクリックで起動します

> EXEは署名されていないため、Windows の SmartScreen やウイルス対策ソフトに警告されることがあります。
> 気になる場合は、ソースコードを確認して、下の B か C を使ってください。

### B. ソースから動かす
```bat
pip install -r requirements.txt
python taskbar_lyrics.py
```

### C. 自分でEXEを作る
`build_exe.bat` をダブルクリックすると、`dist\TaskbarLyrics.exe` ができます（Python 3.12 があれば自動で使います）。
初回は数分かかることがあります。OneDriveの中のフォルダだと、さらに遅くなることがあります。

## 使い方

1. 起動すると、タスクトレイ（時計の近く。`^` の中のこともあります）に、赤い「♪」のアイコンが出ます
2. 「♪」をクリック（タップ）して、メニューの **「位置を合わせる（タップで指定）」** を選びます
3. タスクバーの暗い帯を、**歌詞を出し始める位置 → 出し終わる位置**の順にタップします（アプリのアイコンの右側から、時計・通知の左側まで）
4. Spotify や YouTube で、音楽を再生します。数秒で歌詞が出ます

### メニューの内容

| 項目 | できること |
|---|---|
| （先頭） | いまの曲と、歌詞の取得元（例：LRCLIB（曲名で検索）／行同期） |
| デザイン | 5種類のデザインを切り替え |
| 位置を合わせる | 歌詞を出す範囲を、タップで指定 |
| 表示 | ジャケット／曲名／次の歌詞／一時停止中は薄く／文字サイズ |
| 位置 | 左右へ寄せる／右の余白／タスクバーの上に表示／タブレットモード時の自動調整／リセット |
| この曲のタイミング | この曲だけ、歌詞を早める・遅らせる（±0.1秒、±0.5秒）。曲ごとに保存されます |
| 全曲のタイミング | すべての曲に共通の調整 |
| 全画面アプリ中は隠す | 全画面の動画やゲームの上に出さない |
| Windows起動時に自動起動 | PC起動時に自動で始める |
| 歌詞を一時的に隠す | 表示のオン・オフ |
| 現在の歌詞をコピー | 表示中の歌詞行をクリップボードへ |
| 歌詞の取得元 | LRCLIB のオン・オフ（オフの間は、通信しません）／LyricsPlus のオン・オフ（標準はオフ） |
| 翻訳（DeepL） | 日本語訳を、歌詞の下に表示（APIキーの設定・削除、いまの状態） |
| 歌詞カードを作る… | 歌詞から1〜4行を選んで画像に（コピー／保存） |
| 情報・歌詞データ | LRCLIBを開く／.lrc フォルダを開く／キャッシュ削除／ログ・設定のフォルダを開く／詳細ログ |

## デザイン

| デザイン | 見た目 |
|---|---|
| Apple風 | 歌詞が下からスッと上がってフェードインし、前の行は上に消えます |
| Instagram風 | 丸いラベルの中で、歌詞がポンと弾みます。ラベルの色はジャケット画像から自動で決まります |
| カラオケ風 | 歌うタイミングに合わせて、色が左から流れていきます。単語の時刻があれば単語ごとに、なければ行全体を均等に流します |
| ネオン風 | ジャケット画像の色で、文字が光ります |
| ガラス風 | 半透明の板の上に表示します。背景が明るくても読みやすいです |

## 歌詞の取得について

歌詞は [LRCLIB](https://lrclib.net) から取得します。曲名・アーティスト名の文字列で探すので、表記ゆれや、同名の別の曲に気をつけながら、次の順で探します。

```
再生中の曲（Windowsの再生情報：曲名・アーティスト・アルバム・長さ）
  ├─ 30秒未満・15分超 → 探さない（音楽ではないと判断）
  ├─ 自分の .lrc ファイル（あれば最優先。単語の時刻つきなら、単語同期）
  ├─ ディスクキャッシュ
  │    └─ 一度見つけた歌詞は保存／見つからなかった曲は3日間は再検索しない
  ├─ LRCLIB: 完全一致（アルバム情報があるとき）
  ├─ LRCLIB: 曲名＋アーティスト → 曲名だけ → …（あいまい一致で、表記ゆれに対応）
  ├─ LRCLIB: アーティスト名だけで検索し、曲の長さがほぼ同じものを同じ曲とみなす
  └─ LyricsPlus（オンにしたときだけ。LRCLIBで見つからない曲）
       └─ 返ってきた曲名・アーティスト・長さを、こちらでも確かめる。ディスクには保存しない
見つからない → 表示しない（音楽ではない動画など）
```

| 取得元 | 引き方 | 同期の粒度 |
|---|---|---|
| 自分の .lrc ファイル | 曲名がファイル名に含まれるもの | 行（拡張LRCなら単語） |
| LRCLIB | 曲名・アーティスト・アルバム・長さ | 行 |
| LyricsPlus（任意・標準はオフ） | 曲名・アーティスト・アルバム・長さ | 単語（あれば）／行 |

- 歌詞を採用するのは、**曲の長さがほぼ一致し、曲名も似ているとき**です。MVなどで長さが少しズレる場合は、曲名とアーティストがよく一致するときだけ採用します
- 誤表示を避けるため、条件を満たさない動画には、歌詞を出しません
- LRCLIBへの負荷を減らすため、問い合わせは1曲あたり数回までにしています
- LyricsPlus は、運営チームのルールに合わせて、問い合わせを1曲あたり最大2回にして、歌詞は、ディスクに保存せず、メモリの中でも1時間までしか使い回しません。「見つからなかった」も、ディスクに記憶しません
- 取得元は `Provider` として分けてあるので、増やしやすい作りです（下の「開発」を参照）
- メニューの「歌詞の取得元」で、LRCLIB をオフにできます。オフの間は、何も送りません

いま実際にどこから取得しているかは、トレイの「♪」のメニューを開くと、先頭付近に出ます。

### 単語ごとの同期（拡張LRC）
`%APPDATA%\TaskbarLyrics\lyrics\` に、次のような `.lrc` を置くと、単語同期で表示されます。
```
[00:10.00]<00:10.00>Hello <00:10.50>big <00:11.00>world
[00:12.00]行の時刻だけの行も、混ぜて書けます
```
ファイル名には、曲名を含めてください（例：`アーティスト - 曲名.lrc`）。

## 歌詞の表示

- **曲が変わっても消えない**：探している間は表示を残し、見つかった時点で、曲情報と歌詞を入れ替えます（クロスフェード）
- **カラオケ風の色の流れ**：単語の時刻があれば、単語の進みに合わせて流します。なければ、行の長さに合わせて均等に流します
- **長い行**：幅に収まらないときは、文字を少し小さくして、それでも入らなければ「…」で省略します
- **狭い画面**：幅が足りないときは、まず曲名の表示を畳んで、歌詞を優先します

## 表示速度・軽さのための工夫

- 歌詞の検索は、表示とは別のスレッドで行うので、探している間も画面は止まりません
- 見つけた歌詞は、ディスクキャッシュに残すので、聴き直したときはすぐ出ます。同じ曲のくり返しは、通信をしません
- 再生位置は、取得した基準から画面側で進めます。ズレが大きいときだけ、基準を取り直すので、色の流れや歌詞の切り替わりが、カクつきません
- ブラウザは動画が変わった直後に、本物のジャケットが届く前に、ブラウザのアイコンを返すことがあります。そのため数秒間は取り直して入れ替え、アイコンだと分かった画像は、以後表示しません
- アニメーションは、必要なときだけ1秒に30回描きます

## 歌詞の翻訳（DeepL）

英語などの歌詞に、日本語訳を、1行目の下に小さく表示します（オフが標準です）。

1. [DeepL API](https://www.deepl.com/pro-api) で、自分のAPIキーを用意します（無料版のキーは `:fx` で終わります。申し込みの条件は、DeepLのページで確認してください）
2. メニューの「翻訳（DeepL）」→「歌詞を日本語に翻訳して、下に表示」を選びます。最初に、確認の画面が出ます
3. APIキーを入力します

- 歌詞の文章を、**曲ごとに1回だけ** DeepL に送ります。結果はPCに保存するので、同じ曲では、もう送りません
- 日本語の歌詞は、翻訳しません。DeepLの文字数の上限を、節約するためです
- 「今月の上限に達しました」などのエラーは、メニューの「状態」に出ます
- APIキーは、`settings.json` に保存されます。**このファイルは、他の人に渡さないでください**。メニューの「APIキーを削除」で、消せます
- 翻訳が出ている間は、「次の歌詞を小さく表示」より、翻訳が優先されます

## 歌詞カード

メニューの「歌詞カードを作る…」を選ぶと、いま歌っている行が選ばれた状態で、画面が開きます。行を押すと、最初の行を変えられます。行数は最大4行です。
画像は、ジャケットの色をしいた、正方形（1080×1080）のPNGです。「コピー」か「保存…」を選んでください。画像は、手元のPCで作るだけで、どこにも送信しません。
歌詞の著作権は各権利者に帰属します。画像を公開するときは、短い引用にとどめてください。

## 歌詞が出ないとき・よくある質問

- **歌詞が出ない**：その曲が、LRCLIBに登録されていない可能性があります。自分の `.lrc` を `%APPDATA%\TaskbarLyrics\lyrics\` に置くと使われます。メニューの「情報・歌詞データ」からフォルダを開けます
- **ジャケットがブラウザのアイコンになる**：v1.2.0 以降で、取り直しとアイコンの判定を入れました。最新版を使ってください
- **歌詞が早い・遅い**：メニューの「この曲のタイミング」で、0.1秒単位で調整できます。その曲だけに、保存されます
- **位置が合わない／アイコンと重なる**：「位置を合わせる」で、もう一度指定してください
- **トレイに「♪」が見つからない**：時計の近くの `^` の中を探してください
- **SmartScreenが警告する**：EXEが署名されていないためです。ソースを確認して、自分でビルドもできます
- **全画面の動画で歌詞が出ない**：「全画面アプリ中は隠す」が、オンになっています。メニューから、オフにできます

### ログと設定の場所
すべて `%APPDATA%\TaskbarLyrics\` にあります（メニューの「情報・歌詞データ」→「ログ・設定のフォルダを開く」で開けます）。

| ファイル | 内容 |
|---|---|
| `settings.json` | 設定 |
| `cache.json` | 歌詞のキャッシュ |
| `offsets.json` | 曲ごとのタイミング調整 |
| `translations.json` | 保存してある翻訳 |
| `taskbar_lyrics.log` | 動作のログ（曲名が含まれます。貼る前に確認してください） |
| `lyrics\` | 自分の .lrc ファイル |

### 詳細ログ
不具合を調べるときは、メニューの「情報・歌詞データ」→「詳細ログ（不具合調査用）」をオンにして、もう一度曲を再生してください。どの検索をして、どれを選んだかが、ログに残ります。調べ終わったら、オフに戻してください。

## プライバシー

歌詞の検索のために、**曲名・アーティスト名・アルバム名・曲の長さ**だけを LRCLIB（lrclib.net）に送ります。解析・広告・テレメトリはありません。詳しくは [PRIVACY.md](PRIVACY.md) を参照してください。

## 開発

ビルド不要で、そのまま動かせます。

```bat
python -m py_compile taskbar_lyrics.py
python taskbar_lyrics.py
python -m unittest discover -s tests -t .
```

### 構成
```
taskbar_lyrics.py      起動用のファイル（本体は tblyrics/ の中）
tblyrics/
  core.py              設定・ログ・共有の状態
  lrc.py               歌詞の入れ物（Lyrics）と、LRC／拡張LRCの読み込み
  matching.py          曲名・アーティストのあいまい一致、YouTubeのタイトルの解釈
  cache.py             歌詞のキャッシュ、翻訳の保存、曲ごとのタイミング調整の保存
  translate.py         歌詞の翻訳（DeepL）
  providers.py         歌詞の取得元（自分の .lrc、LRCLIB）と、探す順番
  art.py               ジャケット画像の取り直し、ブラウザのアイコンの見分け
  player.py            Windowsの再生情報を読む作業スレッド（Windows専用）
  bar.py               タスクバーに重ねて描く表示ウィンドウ
  calibrator.py        位置合わせ
  card.py              歌詞カード
  tray.py              タスクトレイとメニュー
  winutil.py           Windows固有の補助（全画面の検知・自動起動など）
  app.py               起動
tests/                 ユニットテスト
```

### 開発のルール
- **既存の機能を壊さない**：変えたあとは、必ず `python -m unittest discover -s tests -t .` を実行します
- **新しい機能は、新しいモジュールで足す**：既存のモジュールに、詰め込みません（翻訳は `translate.py`、歌詞カードは `card.py` のように）
- **直すときは、担当のモジュールで直す**：関係のないファイルに、処理を足しません

### 取得元を増やすには
`tblyrics/providers.py` の `Provider` を継承して `lookup(query)` を書き、`PROVIDERS` に足します。
`lookup` は「`Lyrics` か `None`」と「経路の名前（`error` は通信失敗）」を返します。`tblyrics/lrc.py` の `parse_lrc` を使うと、LRC・拡張LRCを `Lyrics` にできます。
取得元を足す前に、次の基準を確認してください。

- 公開されたAPIで、**利用規約が、第三者のアプリから使うことを、認めている**こと
- 歌詞の権利について、規約や説明が、はっきりしていること
- **歌詞の出どころが、権利者の許可のもとにあること**（商用サービスのログイン情報を使った取得や、無断の収集に頼っていないこと）。APIの説明が公開されていても、データの出どころが確認できないものは、足しません
- **オフにできる**こと（標準でオフが望ましい）。利用者の同意なしに、送信しないこと
- 送る情報が、最小限であること（曲名・アーティスト・長さなど）。ログイン情報や、個人情報は、送らないこと
- 追加したら、`PRIVACY.md` に、送り先と送る内容を書くこと

## コミュニティ・貢献

バグ報告や、歌詞が出ない曲の報告は、[Issues](https://github.com/Nexelo817/taskbar-lyrics/issues) からお願いします（テンプレートがあります）。報告するときは、次の情報があると助かります。

- 再生元（Spotify か YouTube か）と、曲名・アーティスト名
- メニューの先頭に出ている「歌詞: ○○」の表示
- ログ（`taskbar_lyrics.log` の `track:` で始まる行）。ユーザー名などの個人情報は、消してから貼ってください

## 免責・ライセンス・クレジット

- 非公式のツールです。Spotify、Google / YouTube、Microsoft、LRCLIB とは関係ありません
- 歌詞の著作権は各権利者に帰属します。本ツールは歌詞を同梱・再配布せず、利用者自身のPCに表示するだけです。スクリーンショットや動画を公開する際は、歌詞の写り込みにご配慮ください
- 会社・学校の管理下のPCでは、ソフトの導入ルールに従ってください
- 無保証です
- コード：[MIT License](LICENSE)
- 歌詞データ：[LRCLIB](https://lrclib.net) 提供。任意で、[LyricsPlus](https://lyricsplus.prjktla.my.id)
- 使用ライブラリ：[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)（PySide6 は LGPL-3.0）
- 機能の参考：[YTM_Immersion](https://github.com/naikaku1/YTM_Immersion)（MIT License）。コードは、このツール用に新しく書いています

## 更新履歴

[CHANGELOG.md](CHANGELOG.md) を参照してください。

---

## English (short)

**Taskbar Lyrics** shows synced lyrics for the song you're playing (Spotify, YouTube in a browser, etc.) *inside* the Windows taskbar.
It reads the current track from the Windows media session (SMTC), fetches synced lyrics from [LRCLIB](https://lrclib.net), and hides itself for non-music videos.

- 5 visual styles, cover art + title/artist, crossfade between songs (no flicker on track change)
- Optional, off by default: LyricsPlus as a fallback source (used with the LyricsPlus team's permission; word-level sync when available; never stored on disk)
- Shows where the current lyrics came from and whether they are line- or word-synced
- Word-level sync for local enhanced `.lrc` files (karaoke style), per-song timing offsets
- Optional lyrics translation via your own DeepL API key (lyrics text is sent to DeepL once per song; results are cached locally)
- Lyric card: pick 1–4 lines and copy/save them as an image (made locally, never uploaded)
- Tap-to-calibrate placement, touch-friendly tray menu, fullscreen auto-hide, low CPU use
- Fuzzy matching for YouTube titles, on-disk cache, pluggable lyric providers, unit tests
- Only track title / artist / album / duration are sent to LRCLIB. See [PRIVACY.md](PRIVACY.md).

This is a **beta** (v2.3.1-beta.1). Download the EXE from the *Pre-release* on [Releases](https://github.com/Nexelo817/taskbar-lyrics/releases) ("Latest" is the stable v1.2; unsigned: SmartScreen may warn), or run `pip install -r requirements.txt && python taskbar_lyrics.py` (Python 3.9–3.12).
Unofficial; lyrics belong to their rights holders. MIT licensed. Windows 10/11 only for now.
