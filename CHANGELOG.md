# 更新履歴 / Changelog

## v1.2.0
- 修正：ブラウザ（YouTubeなど）で、ジャケット画像の代わりにブラウザのアイコンが表示されることがある問題
  - 動画が変わった直後は、数秒間、画像を取り直して、本物が届いたら入れ替えるようにしました
  - ブラウザのアイコンだと分かった画像は、以後は表示しません
- Fix: the browser's own icon was sometimes shown instead of the cover art (YouTube etc.). The app now re-checks the cover for a few seconds after a track change and hides the browser icon once detected.

## v1.0.1
- 歌詞が見つかる曲を増やしました（曲名の表記ゆれ・YouTubeタイトルの解釈・アーティスト＋長さでの特定）
- 自分の .lrc ファイルに対応、歌詞のキャッシュ、LRCLIBへの問い合わせを減らす工夫
- ログ・設定の保存先を `%APPDATA%\TaskbarLyrics\` に統一

## v1.0.0
- 最初の公開
