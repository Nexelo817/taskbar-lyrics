"""
Taskbar Lyrics  (Surface Go 2 向けに最適化)
- Spotify / ブラウザのYouTube などの再生中の曲を SMTC から取得し、LRCLIB の歌詞をタスクバー内に表示
- 歌詞が無い(=音楽ではない動画など)ときは自動で非表示
- 曲の切り替え時は消えずにクロスフェードで切り替わる
- タスクトレイの「♪」をタップ/クリックで設定メニュー(デザイン・位置・タイミング等)。設定は自動保存

必要なもの:  pip install winsdk requests PySide6
"""
import asyncio
import bisect
import ctypes
import ctypes.wintypes
import difflib
import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
import traceback
import unicodedata
from datetime import datetime, timezone

import requests
from PySide6.QtCore import QRect, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (QAction, QColor, QCursor, QDesktopServices, QFont, QFontMetrics, QIcon,
                           QPainter, QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlayStatus,
)
from winsdk.windows.storage.streams import Buffer, DataReader, InputStreamOptions

# ===== 固定設定 =====
DURATION_TOLERANCE = 5     # 秒。歌詞データの曲長とのズレの許容（音楽判定にも使う）
LATENCY_OFFSET = 0.3       # 秒。歌詞を少し先読み
ANIM_SEC = 0.45            # 行が切り替わるアニメの長さ
HIDE_DELAY = 0.9           # 秒。曲の切れ目の一瞬の途切れでは消さない猶予
POLL_SEC = 0.4             # SMTCを見に行く間隔（省電力のため少し長め）
TABLET_LEFT_RATIO = 0.20   # タブレットモード時はタスクバーのアイコンが少ないので左寄りに

STYLES = [("apple", "Apple風（スライド）"), ("instagram", "Instagram風（ポップ）"),
          ("karaoke", "カラオケ風（色が流れる）"), ("neon", "ネオン風（光る）"),
          ("glass", "ガラス風（半透明の板）")]

# ===== 設定（自動保存）=====
DEFAULTS = {
    "style": "apple", "left_ratio": 0.36, "right_reserved": 280, "above": False,
    "show_cover": True, "show_title": True, "show_next": False, "font_scale": 1.0,
    "dim_paused": True, "offset": 0.0, "hide_fullscreen": True, "hidden": False,
    "auto_tablet": False,
}


def app_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "TaskbarLyrics")


def settings_path():
    return os.path.join(app_dir(), "settings.json")


def load_cfg():
    cfg = dict(DEFAULTS)
    try:
        with open(settings_path(), encoding="utf-8") as f:
            cfg.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
    except Exception:
        pass
    return cfg


def save_cfg():
    try:
        os.makedirs(os.path.dirname(settings_path()), exist_ok=True)
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        log_error()


# ===== ログ =====
def _log_path():
    try:
        os.makedirs(app_dir(), exist_ok=True)
    except OSError:
        pass
    return os.path.join(app_dir(), "taskbar_lyrics.log")


try:
    logging.basicConfig(filename=_log_path(), level=logging.INFO,
                        format="%(asctime)s %(message)s", encoding="utf-8")
except Exception:
    logging.basicConfig(level=logging.INFO)
_last_err = {"msg": None}


def log_error():
    msg = traceback.format_exc()
    if msg != _last_err["msg"]:
        _last_err["msg"] = msg
        logging.error(msg)


cfg = load_cfg()
shared = {"active": False, "title": "", "artist": "", "art": None, "lyrics": None,
          "pos": 0.0, "stamp": 0.0, "playing": True}


# ===== 歌詞取得 =====
APP_VERSION = "1.2.0"
MATCH_VERSION = 2            # 検索ロジックを変えたら上げる（古い「見つからない」の記憶を無効にする）
PROJECT_URL = "https://github.com/Nexelo817/taskbar-lyrics"
LRCLIB = "https://lrclib.net/api"
NEG_TTL = 3 * 24 * 3600      # 見つからなかった曲は3日間は再検索しない（LRCLIBへの負荷を減らす）
MAX_CACHE = 400              # ディスクに残す歌詞キャッシュの最大件数
MIN_DUR, MAX_DUR = 30, 900   # 30秒未満・15分超は音楽ではないとみなして検索しない

_http = requests.Session()
# LRCLIBの推奨に従い、アプリ名とバージョン(と公開URL)をUser-Agentに入れる
_http.headers["User-Agent"] = (f"TaskbarLyrics/{APP_VERSION}"
                               + ("" if "YOUR-NAME" in PROJECT_URL else f" ({PROJECT_URL})"))


def clean_title(t: str) -> str:
    t = re.sub(r"[\(\[【\{（].*?[\)\]】\}）]", " ", t)
    t = re.sub(r"(?i)\s-\s(remaster|live|ver\.|version|mono|stereo|single|edit).*$", " ", t)
    t = re.sub(r"(?i)\b(official|music video|mv|lyrics?|audio|hd|4k)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip(" -|")


def parse_lrc(text: str):
    rows = []
    for raw in text.splitlines():
        stamps = re.findall(r"\[(\d+):(\d+(?:\.\d+)?)\]", raw)
        body = re.sub(r"\[[^\]]*\]", "", raw).strip()
        for m, s in stamps:
            rows.append((int(m) * 60 + float(s), body))
    rows.sort(key=lambda x: x[0])
    return [r[0] for r in rows], [r[1] for r in rows]


def _synced(item):
    if item.get("instrumental"):
        return None
    lrc = item.get("syncedLyrics")
    res = parse_lrc(lrc) if lrc else None
    return res if res and res[0] else None


# --- あいまい一致（表記ゆれに強くして、見つかる曲を増やす）---
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"[\(\[【\{（<＜].*?[\)\]】\}）>＞]", " ", s)
    s = re.sub(r"\b(feat|ft|featuring)\b\.?.*$", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sim(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    lo, hi = sorted((len(a), len(b)))
    if lo >= 3 and (a in b or b in a) and lo / hi >= 0.6:
        r = max(r, 0.9)
    return r


def _artist_parts(a: str):
    return [p for p in re.split(r"\s*(?:,|、|&|＆|／|/|×|feat\.?|ft\.?)\s*", a or "", flags=re.I) if p.strip()]


def artist_sim(a: str, b: str) -> float:
    pa, pb = _artist_parts(a) + [a], _artist_parts(b) + [b]
    return max(sim(x, y) for x in pa for y in pb)


def clean_artist(artist):
    a = re.sub(r"(?i)\s*-\s*topic$", "", artist or "")
    return re.sub(r"(?i)(vevo|\s+official|\s+channel|公式チャンネル|\s*公式)$", "", a).strip()


def guess_pairs(title, artist, has_album):
    """(曲名, アーティスト) の候補を作る。YouTubeの 'Artist - Title' / '【MV】曲名 / Artist' 等に対応"""
    a0 = clean_artist(artist)
    t0 = title or ""
    base = clean_title(t0)
    splits = []
    for m in re.finditer(r"[「『](.+?)[」』]", t0):
        rest = clean_title(re.sub(r"[「『].+?[」』]", " ", t0))
        splits.append((m.group(1).strip(), rest or a0))
    for sep in (r"\s+[-–—―]\s+", r"\s*[/／|｜]\s*"):
        m = re.match(rf"^(.+?){sep}(.+)$", base)
        if m:
            g1, g2 = m.group(1).strip(), m.group(2).strip()
            splits += [(g2, g1), (g1, g2)]
    pairs = [(base, a0)]
    pairs = pairs + splits if has_album else splits + pairs
    out, seen = [], set()
    for T, A in pairs:
        k = (norm(T), norm(A))
        if T and k not in seen:
            seen.add(k)
            out.append((T, A))
    return out[:4]


def score_item(item, T, A, dur):
    """候補を採用するならスコア、しないなら None"""
    d = abs((item.get("duration") or 0) - dur)
    ts = sim(item.get("trackName") or "", T)
    a_s = artist_sim(item.get("artistName") or "", A) if A else 0.5
    if d <= DURATION_TOLERANCE and ts >= 0.6:
        pass                                      # 曲の長さがほぼ一致
    elif d <= 15 and ts >= 0.85 and a_s >= 0.5:   # MVの前後に映像が付く等、長さが少しズレる場合
        pass
    else:
        return None
    return ts * 2 + a_s - d * 0.05


def score_artist(item, A, dur, has_album):
    """曲名の表記が違っても(ローマ字・英語名など)、同じアーティストで長さがほぼ同じなら同じ曲とみなす。
    Spotify(アルバム情報あり)は確実に音楽なので少し緩め、YouTubeは誤判定を避けるため厳しめ。"""
    d = abs((item.get("duration") or 0) - dur)
    a_s = artist_sim(item.get("artistName") or "", A)
    max_d, min_a = (2, 0.8) if has_album else (1, 0.9)
    return a_s - d * 0.1 if (d <= max_d and a_s >= min_a and len(norm(A)) >= 3) else None


# --- ディスクキャッシュ / 自分の .lrc ---
def app_dir_lyrics():
    return os.path.join(app_dir(), "lyrics")


_cache_lock = threading.Lock()
_disk = None


def _cache_path():
    return os.path.join(app_dir(), "cache.json")


def _load_disk():
    global _disk
    if _disk is None:
        try:
            with open(_cache_path(), encoding="utf-8") as f:
                _disk = json.load(f)
        except Exception:
            _disk = {}
    return _disk


def cache_key(title, artist, dur):
    return f"{norm(title)}|{norm(artist)}|{round(dur)}"


def disk_get(key):
    with _cache_lock:
        e = _load_disk().get(key)
    if not e:
        return None
    if e.get("lrc") is None:
        fresh = time.time() - e.get("t", 0) < NEG_TTL and e.get("v") == MATCH_VERSION
        return ("miss", None) if fresh else None
    return ("hit", (e["lrc"][0], e["lrc"][1]))


def disk_put(key, lyrics):
    with _cache_lock:
        d = _load_disk()
        d[key] = {"t": time.time(), "v": MATCH_VERSION,
                  "lrc": [list(lyrics[0]), list(lyrics[1])] if lyrics else None}
        if len(d) > MAX_CACHE:
            for k, _ in sorted(d.items(), key=lambda kv: kv[1].get("t", 0))[:len(d) - MAX_CACHE]:
                d.pop(k, None)
        try:
            os.makedirs(app_dir(), exist_ok=True)
            with open(_cache_path(), "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
        except Exception:
            log_error()


def clear_cache():
    global _disk
    with _cache_lock:
        _disk = {}
        try:
            os.remove(_cache_path())
        except OSError:
            pass


def read_text_file(path):
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    return None


def local_lrc(title, artist):
    """%APPDATA%\\TaskbarLyrics\\lyrics\\ に置いた自分の .lrc ファイルを最優先で使う"""
    d = app_dir_lyrics()
    try:
        files = [f for f in os.listdir(d) if f.lower().endswith(".lrc")]
    except OSError:
        return None
    if not files:
        return None
    pairs = guess_pairs(title, artist, True)[:3]
    best = None
    for f in files:
        stem = norm(os.path.splitext(f)[0])
        for T, _A in pairs:
            nt = norm(T)
            if len(nt) < 2:
                continue
            score = 3 if stem == nt else 2 if nt in stem else 0
            if score and (best is None or score > best[0]):
                best = (score, f)
    if best:
        txt = read_text_file(os.path.join(d, best[1]))
        res = parse_lrc(txt) if txt else None
        if res and res[0]:
            return res
    return None


# --- LRCLIB ---
def lrclib_lookup(title, artist, album, duration):
    errors = ok = 0
    if album:  # Spotifyなどアルバム情報があれば、まず高速な完全一致で
        try:
            r = _http.get(f"{LRCLIB}/get", timeout=6, params={
                "track_name": title, "artist_name": artist,
                "album_name": album, "duration": int(round(duration))})
            if r.status_code == 200:
                ok += 1
                res = _synced(r.json())
                if res:
                    return res, "lrclib-get"
            elif r.status_code == 404:
                ok += 1
            else:
                errors += 1
        except Exception:
            errors += 1
    pairs = guess_pairs(title, artist, bool(album))[:3]
    arts = []
    for A in [clean_artist(artist)] + [p[1] for p in pairs[:2]]:
        if A and A not in arts:
            arts.append(A)
    # 優先順に並べて、LRCLIBへの問い合わせは最大6回まで
    #   (曲名+アーティスト) → (曲名だけ) → ... → (アーティストだけ・長さで特定)
    plan = []
    for n, (T, A) in enumerate(pairs[:3]):
        plan.append((f"{T} {A}".strip(), T, A, "title"))
        if A and n < 2:
            plan.append((T, T, A, "title"))
        if n == 1 and arts:
            plan.append((arts[0], "", arts[0], "artist"))
    if len(pairs) < 2 and arts:
        plan.append((arts[0], "", arts[0], "artist"))
    if len(arts) > 1:
        plan.append((arts[1], "", arts[1], "artist"))
    plan = plan[:6]
    seen = set()
    for q, T, A, mode in plan:
        if q in seen:
            continue
        seen.add(q)
        try:
            r = _http.get(f"{LRCLIB}/search", params={"q": q}, timeout=8)
            r.raise_for_status()
            items = r.json()
            ok += 1
        except Exception:
            errors += 1
            continue
        best = None
        for it in items:
            sc = (score_item(it, T, A, duration) if mode == "title"
                  else score_artist(it, A, duration, bool(album)))
            if sc is not None and (best is None or sc > best[0]):
                res = _synced(it)
                if res:
                    best = (sc, res)
        if best:
            return best[1], "lrclib-search" if mode == "title" else "lrclib-artist"
    if ok == 0 and errors:
        return None, "error"   # 通信失敗。「歌詞なし」として記憶しない
    return None, "none"


def fetch_lyrics(title, artist, album, duration):
    """(歌詞 or None, 取得元) を返す。None なら音楽ではない/歌詞なしとして非表示"""
    if not (MIN_DUR <= duration <= MAX_DUR):
        return None, "skip"
    res = local_lrc(title, artist)
    if res:
        return res, "local"
    key = cache_key(title, artist, duration)
    hit = disk_get(key)
    if hit:
        return hit[1], ("disk-cache" if hit[1] else "negative-cache")
    res, src = lrclib_lookup(title, artist, album, duration)
    if src != "error":
        disk_put(key, res)
    return res, src


def open_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    except Exception:
        log_error()


async def read_thumbnail(info):
    try:
        ref = info.thumbnail
        if not ref:
            return None
        stream = await ref.open_read_async()
        if not stream.size:
            return None
        buf = Buffer(stream.size)
        await stream.read_async(buf, buf.capacity, InputStreamOptions.READ_AHEAD)
        reader = DataReader.from_buffer(buf)
        data = bytearray(buf.length)
        reader.read_bytes(data)
        return bytes(data)
    except Exception:
        return None


BROWSER_IDS = ("chrome", "msedge", "edge", "brave", "firefox", "opera", "vivaldi", "chromium", "iexplore")


def is_browser(session):
    try:
        sid = (session.source_app_user_model_id or "").lower()
    except Exception:
        return False
    return any(b in sid for b in BROWSER_IDS)


class ArtTracker:
    """ジャケット画像の取得をまとめて面倒を見る。
    - ブラウザは動画が変わった直後、本物の画像が届く前に「ブラウザのアイコン」を返すことがある。
      そのため数秒間は取り直して、本物が届いたら入れ替える。
    - 取り直しで画像が入れ替わったら、前の画像はブラウザのアイコンだったと覚えて、以後は出さない。"""
    SCHEDULE = (1.0, 2.5, 4.5, 8.0)   # 曲が変わってから、取り直す時刻(秒)

    def __init__(self):
        self.generic = set()   # ブラウザのアイコンだと分かった画像のハッシュ
        self.reset(None, False)

    def reset(self, key, browser):
        self.key, self.browser = key, browser
        self.t0 = time.perf_counter()
        self.idx = 0
        self.last = 0.0
        self.hash = None

    def accept(self, data):
        """取得した画像を判定して、使う画像(bytes)か、出さない(None)を返す"""
        if not data:
            return None
        h = hashlib.md5(data).hexdigest()
        if self.browser:
            if h in self.generic:
                return None
            if self.hash and self.hash != h:   # 画像が入れ替わった = 前のはアイコンだった
                self.generic.add(self.hash)
                logging.info("cover: browser icon detected, will be hidden from now on")
        self.hash = h
        return data

    def due(self, has_art):
        """いま取り直すべきか"""
        if not self.browser and has_art:
            return False  # Spotify等は、最初に取れていれば取り直さない
        el = time.perf_counter() - self.t0
        if self.idx < len(self.SCHEDULE):
            return el >= self.SCHEDULE[self.idx]
        return (not has_art) and el < 30 and el - self.last >= 2.0  # 画像が無いままなら、30秒までは2秒おきに

    def checked(self):
        self.last = time.perf_counter() - self.t0
        if self.idx < len(self.SCHEDULE):
            self.idx += 1


async def worker():
    mgr = await MediaManager.request_async()
    key = None
    lyrics = None
    cache = {}
    anchor = None      # (再生位置, 取得時刻, 再生中か) 画面側がこれを基準に滑らかに進める
    tracker = ArtTracker()
    retry_after = 0.0
    n = 0
    while True:
        n += 1
        try:
            s = mgr.get_current_session()
            if not s:
                shared["active"] = False  # 曲の切れ目の一瞬の途切れは画面側で吸収
            else:
                info = await s.try_get_media_properties_async()
                tl = s.get_timeline_properties()
                duration = (tl.end_time - tl.start_time).total_seconds()
                k = (info.title, info.artist, round(duration))
                if k != key and time.perf_counter() >= retry_after:
                    key = k
                    anchor = None
                    tracker.reset(k, is_browser(s))
                    shared.update(pos=0.0, stamp=time.perf_counter())
                    was_active = shared["active"]
                    art = None
                    if was_active:  # 表示中なら消さずに、曲情報だけ先に切り替える
                        shared.update(lyrics=None, title=info.title, artist=info.artist)
                        art = tracker.accept(await read_thumbnail(info))
                        shared["art"] = art
                    if k in cache:
                        lyrics, src = cache[k], "memory"
                    else:
                        lyrics, src = await asyncio.to_thread(
                            fetch_lyrics, info.title, info.artist, info.album_title, duration)
                        if src != "error":
                            if len(cache) > 60:
                                cache.clear()
                            cache[k] = lyrics
                    logging.info("track: %r / %r / %.0fs -> %s [%s]", info.title, info.artist,
                                 duration, "FOUND" if lyrics else "none(hidden)", src)
                    if src == "error":  # 通信失敗は20秒後にもう一度試す
                        key = None
                        retry_after = time.perf_counter() + 20
                    if lyrics:
                        if not was_active:
                            art = tracker.accept(await read_thumbnail(info))
                        shared.update(title=info.title, artist=info.artist, art=art, lyrics=lyrics)
                    else:
                        shared["lyrics"] = None
                elif lyrics and tracker.due(shared["art"] is not None):
                    data = await read_thumbnail(info)
                    tracker.checked()
                    if data is not None:            # 取得に失敗したときは今の画像を残す
                        art2 = tracker.accept(data)
                        if art2 != shared["art"]:
                            shared["art"] = art2

                if lyrics:
                    playing = s.get_playback_info().playback_status == PlayStatus.PLAYING
                    pos = tl.position.total_seconds()
                    if playing:
                        pos += (datetime.now(timezone.utc) - tl.last_updated_time).total_seconds()
                    now = time.perf_counter()
                    cand = (pos, now, playing)
                    if anchor and anchor[2] == playing:
                        expected = anchor[0] + ((now - anchor[1]) if playing else 0.0)
                        if abs(pos - expected) > 0.25:  # ズレが大きいときだけ基準を取り直す(カクつき防止)
                            anchor = cand
                    else:
                        anchor = cand
                    shared.update(pos=anchor[0], stamp=anchor[1], playing=playing, active=True)
                else:
                    shared["active"] = False
        except Exception:
            log_error()
        await asyncio.sleep(POLL_SEC)


def start_worker():
    asyncio.run(worker())


# ===== Windows補助 =====
def fullscreen_active():
    try:
        st = ctypes.c_int()
        ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(st))
        return st.value in (2, 3, 4)  # 全画面アプリ / D3D全画面 / プレゼン中
    except Exception:
        return False


def tablet_mode():
    try:
        gm = ctypes.windll.user32.GetSystemMetrics
        return gm(0x56) != 0 and gm(0x2003) == 0  # タブレット対応PCで、スレートモード中
    except Exception:
        return False


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def autostart_cmd():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    exe = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{exe}" "{os.path.abspath(__file__)}"'


def get_autostart():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, "TaskbarLyrics")
        return True
    except Exception:
        return False


def set_autostart(on):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if on:
                winreg.SetValueEx(k, "TaskbarLyrics", 0, winreg.REG_SZ, autostart_cmd())
            else:
                winreg.DeleteValue(k, "TaskbarLyrics")
    except Exception:
        log_error()


# ===== 描画 =====
_fonts = {}


def make_font(px, weight):
    key = (int(px), weight)
    f = _fonts.get(key)
    if f is None:
        f = QFont()
        f.setFamilies(["Segoe UI Variable Display", "Segoe UI", "Yu Gothic UI", "Meiryo UI"])
        f.setPixelSize(max(8, int(px)))
        f.setWeight(weight)
        _fonts[key] = f
    return QFont(f)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


DEFAULT_VIVID = QColor("#5ac8fa")
STYLE_FONT = {"apple": (0.48, QFont.DemiBold), "instagram": (0.42, QFont.ExtraBold),
              "karaoke": (0.46, QFont.Bold), "neon": (0.46, QFont.Bold),
              "glass": (0.44, QFont.DemiBold)}


class Bar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                            | Qt.WindowTransparentForInput | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.lyrics = None
        self.idx = -2
        self.cur = self.prev = self.nxt = ""
        self.line_t0 = 0.0
        self.line_dur = 3.0
        self.p, self.t0 = 1.0, 0.0
        self.master, self.target = 0.0, 0.0
        self.meta = self.prev_meta = None
        self.meta_key = None
        self.meta_p, self.meta_t0 = 1.0, 0.0
        self.accent, self.accent_text, self.vivid = QColor(255, 255, 255), QColor(0, 0, 0), DEFAULT_VIVID
        self.last_active = 0.0
        self.fs_hidden = False
        self.suspended = False
        self._logged_pos = False
        self.place()

        self.anim = QTimer(self, interval=33)       # 30fps。動かす必要があるときだけ回す
        self.anim.timeout.connect(self.tick)
        self.poll = QTimer(self, interval=60)
        self.poll.timeout.connect(self.read_shared)
        self.poll.start()
        self.keep = QTimer(self, interval=800)
        self.keep.timeout.connect(self.keep_on_top)
        self.keep.start()

    # --- 位置: タスクバーに重ねる ---
    def place(self):
        scr = QApplication.primaryScreen()
        g, a = scr.geometry(), scr.availableGeometry()
        y = a.y() + a.height()
        h = g.y() + g.height() - y
        if h < 20:  # タスクバーが下にない/自動で隠す設定のとき
            h = 44
            y = g.y() + g.height() - h
        if cfg["above"]:
            y -= h
        ratio = TABLET_LEFT_RATIO if (cfg["auto_tablet"] and tablet_mode()) else cfg["left_ratio"]
        x = g.x() + int(g.width() * ratio)
        w = g.x() + g.width() - int(cfg["right_reserved"]) - x
        self.setGeometry(QRect(x, y, max(w, 300), h))

    def relayout(self):
        self.place()
        self.update()

    def keep_on_top(self):
        self.fs_hidden = bool(cfg["hide_fullscreen"] and fullscreen_active())
        self.place()
        if not self.isVisible():
            return
        try:
            u = ctypes.windll.user32
            W = ctypes.wintypes
            u.SetWindowPos.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            u.SetWindowPos.restype = W.BOOL
            ok = u.SetWindowPos(W.HWND(int(self.winId())), W.HWND(-1), 0, 0, 0, 0,
                                0x0001 | 0x0002 | 0x0010 | 0x0040)
            if not self._logged_pos:
                self._logged_pos = True
                g = self.geometry()
                logging.info("bar shown: x=%d y=%d w=%d h=%d topmost_ok=%s",
                             g.x(), g.y(), g.width(), g.height(), bool(ok))
        except Exception:
            log_error()

    # --- 状態の取り込み ---
    def pos_now(self):
        s = shared
        t = s["pos"] + ((time.perf_counter() - s["stamp"]) if s["playing"] else 0.0)
        return t + LATENCY_OFFSET + cfg["offset"]

    def read_shared(self):
        s = shared
        now = time.perf_counter()
        if s["active"]:
            self.last_active = now
        alive = s["active"] or (self.last_active and now - self.last_active < HIDE_DELAY)
        if not alive or cfg["hidden"] or self.fs_hidden or self.suspended:
            self.target = 0.0
        elif cfg["dim_paused"] and not s["playing"]:
            self.target = 0.45
        else:
            self.target = 1.0
        if alive:
            key = (s["title"], s["artist"], id(s["art"]))
            if key != self.meta_key:
                self.change_meta(s, key)
        if s["lyrics"] is not self.lyrics:
            self.lyrics = s["lyrics"]
            self.idx = -2
        self.update_line()
        if self.needs_anim() and not self.anim.isActive():
            self.anim.start()

    def change_meta(self, s, key):
        cover = None
        pix = QPixmap()
        if s["art"] and pix.loadFromData(s["art"]):
            cover = pix
            c = pix.toImage().scaled(1, 1, Qt.IgnoreAspectRatio, Qt.SmoothTransformation).pixelColor(0, 0)
            h, sat, v, _ = c.getHsv()
            h = max(h, 0)
            acc = QColor()
            acc.setHsv(h, min(255, int(sat * 1.15)), max(v, 200))
            self.accent = acc
            lum = 0.299 * acc.red() + 0.587 * acc.green() + 0.114 * acc.blue()
            self.accent_text = QColor(0, 0, 0) if lum > 150 else QColor(255, 255, 255)
            if sat > 40:
                viv = QColor()
                viv.setHsv(h, max(sat, 170), 255)
                self.vivid = viv
            else:
                self.vivid = DEFAULT_VIVID
        else:
            self.accent, self.accent_text, self.vivid = QColor(255, 255, 255), QColor(0, 0, 0), DEFAULT_VIVID
        if self.meta is not None and self.master > 0.05 and self.isVisible():
            self.prev_meta = self.meta   # 曲が変わるときはクロスフェード（消えない）
            self.meta_p, self.meta_t0 = 0.0, time.perf_counter()
        self.meta = (s["title"], s["artist"], cover)
        self.meta_key = key

    def update_line(self):
        lyr = self.lyrics
        if lyr:
            times, lines = lyr
            i = bisect.bisect_right(times, self.pos_now()) - 1
        else:
            i = -2
        if i == self.idx:
            return
        self.idx = i
        text = nxt = ""
        if lyr and i >= 0:
            text = lines[i]
            if not text and i < len(lines) - 1:
                text = "♪"
            t1 = times[i + 1] if i + 1 < len(times) else times[i] + 4.0
            self.line_t0 = times[i]
            self.line_dur = max(0.6, min(t1 - times[i], max(1.2, 0.28 * len(text))) * 0.92)
        if lyr:
            for j in range(max(i, -1) + 1, min(max(i, -1) + 4, len(lines))):
                if lines[j]:
                    nxt = lines[j]
                    break
        self.nxt = nxt
        if text != self.cur:
            self.prev, self.cur = self.cur, text
            self.p, self.t0 = 0.0, time.perf_counter()

    def needs_anim(self):
        if self.p < 1 or self.meta_p < 1 or abs(self.target - self.master) > 0.01:
            return True
        return (cfg["style"] == "karaoke" and shared["playing"] and self.master > 0.05
                and bool(self.cur))

    def tick(self):
        now = time.perf_counter()
        if self.p < 1:
            self.p = min(1.0, (now - self.t0) / ANIM_SEC)
            if self.p >= 1:
                self.prev = ""
        if self.meta_p < 1:
            self.meta_p = min(1.0, (now - self.meta_t0) / 0.35)
            if self.meta_p >= 1:
                self.prev_meta = None
        if abs(self.target - self.master) > 0.01:
            self.master += (self.target - self.master) * 0.25
        else:
            self.master = self.target
        if self.master > 0.01 and not self.isVisible():
            self.show()
            self.keep_on_top()
        if self.master <= 0.01 and self.target == 0.0 and self.isVisible():
            self.hide()
            self.cur = self.prev = self.nxt = ""
            self.idx, self.meta, self.meta_key, self.prev_meta = -2, None, None, None
        if self.isVisible():
            self.update()
        if not self.needs_anim():
            self.anim.stop()

    # --- 描画 ---
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        W, H = self.width(), self.height()
        style = cfg["style"]
        p.setOpacity(self.master)
        if style == "glass":
            p.setPen(QPen(QColor(255, 255, 255, 45), 1))
            p.setBrush(QColor(24, 24, 28, 185))
            p.drawRoundedRect(QRectF(1.5, 3, W - 3, H - 6), 11, 11)

        cs = H - 10 if cfg["show_cover"] else 0
        tw = min(190, int(W * 0.26)) if cfg["show_title"] else 0
        base = 10 + (cs + 10 if cs else 0)
        if tw and W - base - tw - 26 < 260:  # 狭い画面(Surface Go 2等)ではまず曲名を畳む
            tw = 0
        lx = base + (tw + 16 if tw else 4)
        area = QRectF(lx, 0, W - lx - 10, H)

        em = ease_out(self.meta_p)
        if self.prev_meta is not None:
            self.draw_meta(p, self.prev_meta, 1 - em, 10, H, cs, tw)
            self.draw_meta(p, self.meta, em, 10, H, cs, tw)
        else:
            self.draw_meta(p, self.meta, 1.0, 10, H, cs, tw)

        e = ease_out(self.p)
        two = cfg["show_next"]
        cy = H * 0.38 if two else H / 2
        pr = None
        if style == "karaoke" and self.idx >= 0:
            pr = min(1.0, max(0.0, (self.pos_now() - self.line_t0) / self.line_dur))
        if style == "instagram":
            self.draw_lyric(p, self.prev, area, cy, max(0.0, 1 - self.p * 4), 0, 1.0)
            self.draw_lyric(p, self.cur, area, cy, min(1.0, self.p * 3), 0, 0.8 + 0.2 * ease_back(self.p))
        else:
            self.draw_lyric(p, self.prev, area, cy, max(0.0, 1 - e * 1.6), -e * H * 0.35, 1.0,
                            1.0 if style == "karaoke" else None)
            self.draw_lyric(p, self.cur, area, cy, e, (1 - e) * H * 0.35, 1.0, pr)
        if two:
            self.draw_next(p, area, H, e)

    def draw_meta(self, p, meta, alpha, x, H, cs, tw):
        if meta is None or alpha <= 0.01:
            return
        title, artist, cover = meta
        p.save()
        p.setOpacity(self.master * alpha)
        if cs:
            r = QRectF(x, (H - cs) / 2, cs, cs)
            path = QPainterPath()
            path.addRoundedRect(r, 6, 6)
            if cover is not None:
                side = min(cover.width(), cover.height())
                src = QRect((cover.width() - side) // 2, (cover.height() - side) // 2, side, side)
                p.setClipPath(path)
                p.drawPixmap(r.toRect(), cover, src)
                p.setClipping(False)
            else:
                p.fillPath(path, QColor(255, 255, 255, 30))
        if tw:
            tx = x + (cs + 10 if cs else 0)
            f1, f2 = make_font(H * 0.31, QFont.DemiBold), make_font(H * 0.26, QFont.Normal)
            m1, m2 = QFontMetrics(f1), QFontMetrics(f2)
            y0 = (H - (m1.height() + m2.height())) / 2
            p.setFont(f1)
            p.setPen(QColor(255, 255, 255, 235))
            p.drawText(QRectF(tx, y0, tw, m1.height()), Qt.AlignLeft | Qt.AlignVCenter,
                       m1.elidedText(title, Qt.ElideRight, tw))
            p.setFont(f2)
            p.setPen(QColor(255, 255, 255, 150))
            p.drawText(QRectF(tx, y0 + m1.height(), tw, m2.height()), Qt.AlignLeft | Qt.AlignVCenter,
                       m2.elidedText(artist, Qt.ElideRight, tw))
        p.restore()

    def draw_next(self, p, area, H, alpha):
        if not self.nxt or alpha <= 0.01:
            return
        font = make_font(H * 0.22 * cfg["font_scale"], QFont.Normal)
        fm = QFontMetrics(font)
        p.save()
        p.setOpacity(self.master * alpha)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 140))
        p.drawText(QRectF(area.x(), H * 0.82 - fm.height() / 2, area.width(), fm.height()),
                   Qt.AlignHCenter | Qt.AlignVCenter, fm.elidedText(self.nxt, Qt.ElideRight, int(area.width() - 8)))
        p.restore()

    def draw_lyric(self, p, text, area, cy, alpha, dy, scale, progress=None):
        if not text or alpha <= 0.01:
            return
        style = cfg["style"]
        mult, weight = STYLE_FONT[style]
        px = self.height() * mult * cfg["font_scale"] * (0.78 if cfg["show_next"] else 1.0)
        font = make_font(px, weight)
        pad = 12 if style == "instagram" else 0
        avail = area.width() - pad * 2 - 8
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(text)
        if w > avail:  # 長い行は縮小し、それでも入らなければ省略
            font = make_font(px * max(0.7, avail / w), weight)
            fm = QFontMetrics(font)
            text = fm.elidedText(text, Qt.ElideRight, int(avail))
            w = fm.horizontalAdvance(text)
        h = fm.height()
        p.save()
        p.setOpacity(self.master * alpha)
        p.translate(area.center().x(), cy + dy)
        p.scale(scale, scale)
        p.setFont(font)
        r = QRectF(-w / 2 - 2, -h / 2, w + 4, h)
        if style == "instagram":
            p.setPen(Qt.NoPen)
            p.setBrush(self.accent)
            p.drawRoundedRect(QRectF(-w / 2 - pad, -h / 2 - 3, w + pad * 2, h + 6), 9, 9)
            p.setPen(self.accent_text)
            p.drawText(r, Qt.AlignCenter, text)
        elif style == "neon":
            path = QPainterPath()
            path.addText(-w / 2, -h / 2 + fm.ascent(), font, text)
            v = self.vivid
            p.setBrush(Qt.NoBrush)
            for width, a in ((10, 26), (6, 48), (3, 90)):
                p.setPen(QPen(QColor(v.red(), v.green(), v.blue(), a), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.drawPath(path)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255))
            p.drawPath(path)
        elif style == "karaoke":
            p.setPen(QColor(255, 255, 255, 120))
            p.drawText(r, Qt.AlignCenter, text)
            if progress:
                p.setClipRect(QRectF(-w / 2 - 4, -h, w * progress + 4, h * 2))
                p.setPen(self.vivid)
                p.drawText(r, Qt.AlignCenter, text)
        else:  # apple / glass
            p.setPen(QColor(0, 0, 0, 110))
            p.drawText(r.translated(0, 1), Qt.AlignCenter, text)
            p.setPen(QColor(255, 255, 255))
            p.drawText(r, Qt.AlignCenter, text)
        p.restore()


# ===== 位置合わせ（タップで指定）=====
def force_topmost(widget):
    try:
        u = ctypes.windll.user32
        W = ctypes.wintypes
        u.SetWindowPos.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        u.SetWindowPos(W.HWND(int(widget.winId())), W.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0040)
    except Exception:
        pass


class Calibrator(QWidget):
    """タスクバーに暗い帯を出し、歌詞の「開始位置」と「終了位置」を2回タップして決める"""
    HINTS = ("① 歌詞を出し始める位置をタップ（アプリのアイコンの右側）",
             "② 歌詞を出し終わる位置をタップ（時計・通知の左側）")

    def __init__(self, bar):
        super().__init__()
        self.bar = bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.g = QApplication.primaryScreen().geometry()
        self.setGeometry(self.g.x(), bar.y(), self.g.width(), bar.height())
        self.stage, self.x1, self.msg, self.done = 0, None, "", False
        bar.suspended = True
        QTimer.singleShot(30000, self.finish)  # 30秒で自動キャンセル
        self.show()
        force_topmost(self)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 190))
        if self.x1 is not None:
            p.fillRect(QRect(int(self.x1 - self.g.x()), 0, 3, self.height()), QColor("#5ac8fa"))
        p.setPen(Qt.white)
        p.setFont(make_font(self.height() * 0.38, QFont.DemiBold))
        p.drawText(self.rect(), Qt.AlignCenter, self.msg or self.HINTS[self.stage])

    def mousePressEvent(self, e):
        gx = e.globalPosition().x()
        if self.stage == 0:
            self.x1, self.stage, self.msg = gx, 1, ""
            self.update()
            return
        if gx < self.x1 + 300:
            self.msg = "もう少し右をタップしてください"
            self.update()
            return
        cfg["left_ratio"] = round((self.x1 - self.g.x()) / self.g.width(), 3)
        cfg["right_reserved"] = int(self.g.x() + self.g.width() - gx)
        save_cfg()
        self.finish()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.finish()

    def finish(self):
        if self.done:
            return
        self.done = True
        self.bar.suspended = False
        self.bar.relayout()
        self.close()


# ===== タスクトレイ =====
def make_icon():
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#fa2d48"))
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    p.setPen(Qt.white)
    p.setFont(QFont("Segoe UI Symbol", 30, QFont.Bold))
    p.drawText(pm.rect(), Qt.AlignCenter, "♪")
    p.end()
    return QIcon(pm)


MENU_QSS = """
QMenu { background:#2b2b2e; color:#f2f2f7; border:1px solid #48484a; padding:6px; font-size:14px; }
QMenu::item { padding:10px 28px 10px 20px; border-radius:6px; }
QMenu::item:selected { background:#0a84ff; }
QMenu::item:disabled { color:#8e8e93; }
QMenu::separator { height:1px; background:#48484a; margin:6px 8px; }
"""


def build_tray(app, bar):
    tray = QSystemTrayIcon(make_icon(), app)
    tray.setToolTip(f"Taskbar Lyrics v{APP_VERSION}")
    menu = QMenu()
    menu.setStyleSheet(MENU_QSS)
    subs = []

    def setv(k, v):
        cfg[k] = v
        save_cfg()
        bar.relayout()

    def tog(k):
        setv(k, not cfg[k])

    def add(m, label, fn, on=None):
        text = label if on is None else (("✔  " if on else "      ") + label)
        a = m.addAction(text)
        a.triggered.connect(lambda _=False, f=fn: f())
        return a

    def sub(title):
        s = menu.addMenu(title)
        subs.append(s)
        return s

    def shift(d):
        setv("left_ratio", round(min(0.9, max(0.0, cfg["left_ratio"] + d)), 3))

    def margin(d):
        setv("right_reserved", max(0, int(cfg["right_reserved"] + d)))

    def timing(d):
        setv("offset", 0.0 if d is None else round(cfg["offset"] + d, 1))

    def reset_pos():
        cfg["left_ratio"], cfg["right_reserved"], cfg["above"] = (
            DEFAULTS["left_ratio"], DEFAULTS["right_reserved"], DEFAULTS["above"])
        save_cfg()
        bar.relayout()

    def calibrate():
        bar.calib = Calibrator(bar)

    def toggle_autostart():
        set_autostart(not get_autostart())

    def rebuild():
        for s in subs:
            s.deleteLater()
        subs.clear()
        menu.clear()
        m = bar.meta
        head = menu.addAction(f"♪ {m[0]} — {m[1]}" if m and bar.target > 0 else "♪ Taskbar Lyrics")
        head.setEnabled(False)
        menu.addSeparator()

        d = sub("デザイン")
        for key, label in STYLES:
            add(d, label, lambda k=key: setv("style", k), cfg["style"] == key)

        add(menu, "位置を合わせる（タップで指定）", calibrate)
        v = sub("表示")
        add(v, "ジャケット画像", lambda: tog("show_cover"), cfg["show_cover"])
        add(v, "曲名・アーティスト名", lambda: tog("show_title"), cfg["show_title"])
        add(v, "次の歌詞も小さく表示", lambda: tog("show_next"), cfg["show_next"])
        add(v, "一時停止中は薄く", lambda: tog("dim_paused"), cfg["dim_paused"])
        v.addSeparator()
        for label, val in (("文字: 小", 0.85), ("文字: 標準", 1.0), ("文字: 大", 1.2)):
            add(v, label, lambda x=val: setv("font_scale", x), abs(cfg["font_scale"] - val) < 0.01)

        ps = sub("位置")
        add(ps, "位置を合わせる（タップで指定）", calibrate)
        ps.addSeparator()
        add(ps, "← 左へ寄せる", lambda: shift(-0.03))
        add(ps, "→ 右へ寄せる", lambda: shift(0.03))
        add(ps, "右の余白を増やす（時計に被るとき）", lambda: margin(40))
        add(ps, "右の余白を減らす", lambda: margin(-40))
        add(ps, "タスクバーの上に表示（重ねない）", lambda: tog("above"), cfg["above"])
        add(ps, "タブレットモード時は自動で左へ広げる", lambda: tog("auto_tablet"), cfg["auto_tablet"])
        add(ps, "位置をリセット", reset_pos)

        t = sub(f"歌詞のタイミング（今: {cfg['offset']:+.1f}秒）")
        add(t, "0.5秒 早く出す", lambda: timing(0.5))
        add(t, "0.5秒 遅く出す", lambda: timing(-0.5))
        add(t, "0.1秒 早く出す", lambda: timing(0.1))
        add(t, "0.1秒 遅く出す", lambda: timing(-0.1))
        add(t, "リセット", lambda: timing(None))

        menu.addSeparator()
        add(menu, "全画面アプリ中は隠す", lambda: tog("hide_fullscreen"), cfg["hide_fullscreen"])
        add(menu, "Windows起動時に自動起動", toggle_autostart, get_autostart())
        add(menu, "歌詞を一時的に隠す", lambda: tog("hidden"), cfg["hidden"])
        add(menu, "現在の歌詞をコピー", lambda: QApplication.clipboard().setText(bar.cur))
        i = sub("情報・歌詞データ")
        i.addAction(f"Taskbar Lyrics v{APP_VERSION}").setEnabled(False)
        add(i, "歌詞データ提供: LRCLIB（lrclib.net）を開く",
            lambda: QDesktopServices.openUrl(QUrl("https://lrclib.net")))
        add(i, "自分の .lrc を置くフォルダを開く", lambda: open_dir(app_dir_lyrics()))
        add(i, "歌詞キャッシュを削除", clear_cache)
        add(i, "ログ・設定のフォルダを開く", lambda: open_dir(app_dir()))
        if "YOUR-NAME" not in PROJECT_URL:
            add(i, "プロジェクトページを開く", lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))
        menu.addSeparator()
        add(menu, "終了", app.quit)

    menu.aboutToShow.connect(rebuild)
    rebuild()
    tray.setContextMenu(menu)
    # タッチ操作でも開けるように、通常のタップ/クリックでもメニューを出す
    tray.activated.connect(lambda r: menu.popup(QCursor.pos()) if r == QSystemTrayIcon.Trigger else None)
    tray.show()
    return tray, menu, rebuild


def main():
    logging.info("start v%s", APP_VERSION)
    sys.excepthook = lambda *a: logging.error("".join(traceback.format_exception(*a)))
    try:  # 二重起動の防止
        ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\TaskbarLyricsSingleton")
        if ctypes.windll.kernel32.GetLastError() == 183:
            logging.info("already running")
            return
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    threading.Thread(target=start_worker, daemon=True).start()
    bar = Bar()
    app._keep = (bar, *build_tray(app, bar))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
