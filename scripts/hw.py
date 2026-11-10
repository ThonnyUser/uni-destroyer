#!/usr/bin/env python3
"""hw.py - local helper for the homework-vault skill.

Gathers material only. The calling LLM reads it and writes the summary.
Output goes to HW_VAULT if set, otherwise to ~/Downloads/homework-vault.
"""
import argparse
import datetime as dt
import os
import pathlib
import re
import sys
import time


def vault():
    v = os.environ.get("HW_VAULT")
    p = pathlib.Path(v).expanduser() if v else pathlib.Path.home() / "Downloads" / "homework-vault"
    p.mkdir(parents=True, exist_ok=True)
    return p


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^\w\-]+", "-", s.strip())).strip("-").lower() or "untitled"


def safe(name):
    """Folder or file name from a course name: keeps case and spaces, drops characters Windows forbids."""
    return re.sub(r'[<>:"/\|?*]+', "", name).strip() or "course"


def cdir(course):
    """The one folder that holds everything for a course, named like 'ELEC1111 Vault'."""
    name = safe(course)
    if not name.lower().endswith("vault"):
        name += " Vault"
    return vault() / name


def stamp():
    return dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def sub(course, name):
    d = cdir(course) / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_shot(a):
    import mss
    import mss.tools

    if a.delay:
        time.sleep(a.delay)
    out = sub(a.course, "attachments") / f"{stamp()}-{slug(a.label)}.png"
    with mss.mss() as s:
        area = s.monitors[a.monitor]
        if a.region:
            x, y, w, h = a.region
            area = {"left": x, "top": y, "width": w, "height": h}
        img = s.grab(area)
        mss.tools.to_png(img.rgb, img.size, output=str(out))
    print(out)
    print(f"![[{out.name}]]")
    if a.ocr:
        print(_ocr(out, a.course))


def _ocr(image, course):
    from rapidocr_onnxruntime import RapidOCR

    result, _ = RapidOCR()(str(image))
    lines = [r[1] for r in (result or [])]
    out = sub(course, "sources") / f"{pathlib.Path(image).stem}-ocr.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def cmd_ocr(a):
    print(_ocr(a.file, a.course))


def _transcribe(path, course, model_name):
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, compute_type="int8")
    segments, _ = model.transcribe(str(path))
    out = sub(course, "sources") / f"{stamp()}-{slug(pathlib.Path(path).stem)}.txt"
    with open(out, "w", encoding="utf-8") as f:
        for s in segments:
            m, sec = divmod(int(s.start), 60)
            f.write(f"[{m:02d}:{sec:02d}] {s.text.strip()}\n")
    return out


def cmd_transcribe(a):
    print(_transcribe(a.file, a.course, a.model))


def cmd_record(a):
    import wave

    import numpy as np
    import sounddevice as sd

    chunks = []
    rate = 16000

    def cb(data, frames, t, status):
        chunks.append(data.copy())

    print("Recording. Press Ctrl+C to stop.", file=sys.stderr)
    try:
        with sd.InputStream(samplerate=rate, channels=1, dtype="int16", callback=cb):
            while True:
                time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    if not chunks:
        sys.exit("No audio captured.")
    wav = sub(a.course, "sources") / f"{stamp()}-live.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.concatenate(chunks).tobytes())
    print(_transcribe(wav, a.course, a.model))


def cmd_slides(a):
    p = pathlib.Path(a.file)
    ext = p.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        parts = [f"## Page {i}\n{pg.extract_text() or ''}" for i, pg in enumerate(PdfReader(p).pages, 1)]
    elif ext == ".pptx":
        from pptx import Presentation

        parts = []
        for i, sl in enumerate(Presentation(p).slides, 1):
            txt = "\n".join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)
            parts.append(f"## Slide {i}\n{txt}")
    else:
        parts = [p.read_text(encoding="utf-8", errors="replace")]
    out = sub(a.course, "sources") / f"{stamp()}-{slug(p.stem)}.txt"
    out.write_text("\n\n".join(parts), encoding="utf-8")
    print(out)


def cmd_note(a):
    body = sys.stdin.read().strip()
    if not body:
        sys.exit("Pipe the markdown note into stdin.")
    d = sub(a.course, "notes")
    out = d / f"{dt.date.today()}-{a.kind}-{slug(a.title)}.md"
    head = f"---\ncourse: {a.course}\nkind: {a.kind}\ndate: {dt.date.today()}\n---\n\n"
    out.write_text(head + body + "\n", encoding="utf-8")
    print(out)


def cmd_save(a):
    text = sys.stdin.read().strip()
    if not text:
        sys.exit("Pipe the text into stdin.")
    out = sub(a.course, "sources") / f"{stamp()}-{slug(a.label)}.md"
    head = f"Source: {a.source}\n\n" if a.source else ""
    out.write_text(head + text + "\n", encoding="utf-8")
    print(out)


def cmd_fetch(a):
    import trafilatura
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urldefrag, urlparse

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.found = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                for k, v in attrs:
                    if k == "href" and v:
                        self.found.append(v)

    host = urlparse(a.url).netloc
    seen, queue = set(), [(a.url, 0)]
    while queue and len(seen) < a.max_pages:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        html = trafilatura.fetch_url(url)
        if not html:
            print(f"skipped (no download): {url}", file=sys.stderr)
            continue
        text = trafilatura.extract(html, include_links=True, output_format="markdown") or ""
        if not text.strip():
            print(f"skipped (no text, page may need a login or JavaScript): {url}", file=sys.stderr)
        else:
            u = urlparse(url)
            out = sub(a.course, "sources") / f"{stamp()}-{slug(u.netloc + u.path)[:60]}.md"
            out.write_text(f"Source: {url}\n\n{text}\n", encoding="utf-8")
            print(out)
        if depth < a.depth:
            p = Links()
            p.feed(html)
            for href in p.found:
                link = urldefrag(urljoin(url, href))[0]
                if link.startswith("http") and urlparse(link).netloc == host and link not in seen:
                    queue.append((link, depth + 1))


def cmd_captions(a):
    import glob

    import yt_dlp

    d = sub(a.course, "sources")
    tag = stamp()
    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [a.lang],
        "subtitlesformat": "vtt",
        "outtmpl": str(d / f"{tag}-%(id)s.%(ext)s"),
        "quiet": True,
        "noprogress": True,
    }
    vtts = []
    for attempt in range(a.retries):
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                y.download([a.url])
        except Exception as e:
            print(f"caption download failed: {e}", file=sys.stderr)
        vtts = glob.glob(str(d / f"{tag}-*.vtt"))
        if vtts:
            break
        if attempt + 1 < a.retries:
            wait = 45 * (attempt + 1)  # YouTube answers HTTP 429 when asked too fast
            print(f"waiting {wait}s then retrying", file=sys.stderr)
            time.sleep(wait)
    if vtts:
        lines, last = [], ""
        for raw in open(vtts[0], encoding="utf-8"):
            t = re.sub(r"<[^>]+>", "", raw).strip()
            if not t or t.startswith(("WEBVTT", "Kind:", "Language:")) or "-->" in t:
                continue
            if t != last:
                lines.append(t)
                last = t
        out = pathlib.Path(vtts[0]).with_suffix(".txt")
        out.write_text("\n".join(lines), encoding="utf-8")
        for v in vtts:
            os.remove(v)
        print(out)
        return
    if a.captions_only:
        sys.exit("No captions found (skipped audio download).")
    print("No captions found. Downloading audio to transcribe.", file=sys.stderr)
    opts = {"format": "bestaudio", "outtmpl": str(d / f"{tag}-%(id)s.%(ext)s"), "quiet": True, "noprogress": True}
    with yt_dlp.YoutubeDL(opts) as y:
        y.download([a.url])
    audio = [p for p in glob.glob(str(d / f"{tag}-*")) if not p.endswith(".txt")]
    if not audio:
        sys.exit("Download failed.")
    print(_transcribe(audio[0], a.course, a.model))


SEED_TERMS = """malloc calloc realloc free scanf printf fgets fprintf sprintf strcpy strncpy strlen strcmp
strcat typedef struct enum sizeof stdin stdout stderr argv argc""".split()


def cmd_fixcaptions(a):
    """Fix speech-to-text errors with the course's own vocabulary. Unsure cases are marked [ambiguous]."""
    from difflib import SequenceMatcher

    src = cdir(a.course) / "sources"
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in src.glob("*.md")) if src.exists() else ""
    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
    terms = {w for w in words if len(w) >= 4 and ("_" in w or re.search(r"[a-z][A-Z]", w))}
    terms |= set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", text))
    terms |= set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\(\)", text))
    terms |= set(SEED_TERMS)
    if a.terms:
        terms |= {t.strip() for t in open(a.terms, encoding="utf-8") if t.strip()}
    terms = {t for t in terms if not t.isupper()}  # skip CONSTANTS: they match ordinary English words
    known = {w.lower() for w in words}
    canon = {t.lower(): t for t in terms}
    log = []
    p = pathlib.Path(a.file)
    body = p.read_text(encoding="utf-8", errors="replace")
    freq = {}
    for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", body):
        freq[w.lower()] = freq.get(w.lower(), 0) + 1
    small = {"to", "is", "in", "it", "of", "on", "at", "as", "an", "or", "be", "by", "do", "go", "if", "so",
             "no", "we", "up", "my", "me", "he", "us", "am"}

    def best(tok):
        low = tok.lower()
        # a word said many times is almost surely a real word, not a one-off mishearing
        if len(low) < 5 or low in known or low in canon or freq.get(low, 0) >= 3:
            return None, 0
        if any(low[:-k] in known for k in (1, 2, 3)):  # plain inflection of a real word: coded, breaks
            return None, 0
        same = [c for c in canon if c[0] == low[0]]  # a mishearing keeps its first letter
        if not same:
            return None, 0
        score, pick = max((SequenceMatcher(None, low, c).ratio(), c) for c in same)
        return pick, score

    def join_pair(m):
        joined = (m.group(1) + m.group(2)).lower()
        if m.group(1).lower() in small or m.group(2).lower() in small:
            return m.group(0)
        if joined in canon and m.group(0).lower() not in canon:
            log.append(f"joined '{m.group(0)}' -> '{canon[joined]}'")
            return canon[joined]
        return m.group(0)

    def fix_word(m):
        tok = m.group(0)
        pick, score = best(tok)
        if pick and score >= a.fix_at:
            log.append(f"fixed '{tok}' -> '{canon[pick]}' ({score:.2f})")
            return canon[pick]
        if pick and score >= a.flag_at and len(tok) >= 6:
            log.append(f"AMBIGUOUS '{tok}' maybe '{canon[pick]}' ({score:.2f})")
            return f"{tok} [ambiguous: maybe {canon[pick]}]"
        return tok

    body = re.sub(r"\b([A-Za-z]{2,}) ([A-Za-z]{1,})\b", join_pair, body)
    body = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", fix_word, body)
    out = p.with_suffix(".corrected.txt")
    out.write_text(body, encoding="utf-8")
    logf = p.with_suffix(".corrections.txt")
    logf.write_text("\n".join(log) or "no changes", encoding="utf-8")
    fixed = sum(1 for x in log if x.startswith(("fixed", "joined")))
    print(out)
    print(f"{fixed} fixed, {len(log) - fixed} ambiguous. Log: {logf}")


def _browser():
    """Path of Edge or Chrome, or None."""
    import shutil

    names = ["msedge", "chrome", "google-chrome", "chromium"]
    paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    return next((shutil.which(n) for n in names if shutil.which(n)), None) or next(
        (p for p in paths if os.path.exists(p)), None)


def _rendered(url):
    """Page HTML after JavaScript runs (headless Edge or Chrome). Falls back to a plain download."""
    import subprocess
    import tempfile

    exe = _browser()
    if exe:
        try:
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
                r = subprocess.run([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={prof}",
                                    "--virtual-time-budget=8000", "--dump-dom", url],
                                   capture_output=True, timeout=90)
            html = r.stdout.decode("utf-8", errors="replace")
            if "<html" in html.lower():
                return html
        except Exception:
            pass
    import trafilatura

    return trafilatura.fetch_url(url) or ""


FILE_EXT = (".pdf", ".pptx", ".ppt", ".docx", ".doc", ".txt", ".c", ".h", ".py", ".ipynb", ".csv", ".zip")
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".ico", ".woff", ".woff2", ".mp4")
YT_ID = re.compile(r"(?:youtube\.com/(?:watch\?v=|live/|embed/)|youtu\.be/)([\w-]{11})")


def cmd_grab(a):
    """Download only: pages as text, linked files, video captions. No summaries, no LLM, no tokens."""
    import argparse as ap_
    import trafilatura
    import urllib.request
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urldefrag, urlparse

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.found = []

        def handle_starttag(self, tag, attrs):
            for k, v in attrs:
                if k in ("href", "src") and v:
                    self.found.append(v)

    host = urlparse(a.url).netloc
    seen, queue = set(), [(a.url, 0)]
    pages, files, videos = [], {}, {}
    while queue and len(seen) < a.max_pages:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        html = _rendered(url)
        if not html:
            print(f"skipped (could not load): {url}", file=sys.stderr)
            continue
        text = trafilatura.extract(html, include_links=True, output_format="markdown") or ""
        if text.strip():
            u = urlparse(url)
            out = sub(a.course, "sources") / f"{stamp()}-{slug(u.netloc + u.path)[:60]}.md"
            out.write_text(f"Source: {url}\n\n{text}\n", encoding="utf-8")
            pages.append((url, out))
            print(f"page: {out.name}")
        for m in YT_ID.finditer(html):
            videos.setdefault(m.group(1), url)
        p = Links()
        p.feed(html)
        for href in p.found:
            link = urldefrag(urljoin(url, href))[0]
            if not link.startswith("http"):
                continue
            path = urlparse(link).path.lower()
            if path.endswith(FILE_EXT):
                if urlparse(link).netloc == host:
                    files.setdefault(link, url)
            elif not path.endswith(SKIP_EXT) and urlparse(link).netloc == host and depth < a.depth \
                    and link not in seen and all(q[0] != link for q in queue):
                queue.append((link, depth + 1))

    got = []
    fdir = sub(a.course, "attachments") / "files"
    fdir.mkdir(parents=True, exist_ok=True)
    for link in files:
        name = slug(pathlib.Path(urlparse(link).path).stem) + pathlib.Path(urlparse(link).path).suffix.lower()
        dest = fdir / name
        try:
            with urllib.request.urlopen(link, timeout=60) as r:
                data = r.read(a.max_mb * 1024 * 1024 + 1)
            if len(data) > a.max_mb * 1024 * 1024:
                print(f"skipped (over {a.max_mb} MB): {link}", file=sys.stderr)
                continue
            dest.write_bytes(data)
            got.append((link, dest))
            print(f"file: {dest.name}")
        except Exception as e:
            print(f"skipped file {link}: {e}", file=sys.stderr)

    vids = []
    if a.videos:
        for vid, src in videos.items():
            ns = ap_.Namespace(url=f"https://www.youtube.com/watch?v={vid}", course=a.course, lang="en",
                               model="small", captions_only=True, retries=3)
            try:
                cmd_captions(ns)
                vids.append((vid, "captions saved"))
            except SystemExit as e:
                vids.append((vid, f"no captions ({e})"))
            time.sleep(a.pace)

    idx = cdir(a.course) / "index.md"
    lines = [f"# Download index for {a.url}", "", f"## Pages ({len(pages)})"]
    lines += [f"- {u} -> sources/{o.name}" for u, o in pages]
    lines += ["", f"## Files ({len(got)})"] + [f"- {u} -> attachments/files/{d.name}" for u, d in got]
    lines += ["", f"## Videos found ({len(videos)})"]
    lines += [f"- https://www.youtube.com/watch?v={v} (on {s})" + (f": {dict(vids).get(v, 'not fetched')}" if a.videos else "")
              for v, s in videos.items()]
    idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(pages)} pages, {len(got)} files, {len(videos)} videos found. Index: {idx}")


def cmd_webshot(a):
    """Picture of a web page only (not the desktop), using headless Edge or Chrome."""
    import subprocess

    exe = _browser()
    if not exe:
        sys.exit("No Edge or Chrome found. Use `shot` instead.")
    out = sub(a.course, "attachments") / f"{stamp()}-{slug(a.label)}.png"
    import tempfile

    # a throwaway profile makes the browser start fresh even if the user's browser is open
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={prof}", f"--window-size={a.width},{a.height}",
                        f"--screenshot={out}", a.url],
                       timeout=90, capture_output=True)
        for _ in range(240):  # the browser may hand the work to a child process
            if out.exists() and out.stat().st_size > 0:
                break
            time.sleep(0.5)
    if not out.exists():
        sys.exit("Browser made no screenshot.")
    print(out)
    print(f"![[{out.name}]]")


def _latin(text):
    """Core PDF fonts are latin-1 only: swap common symbols, drop the rest."""
    for k, v in {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-",
                 "—": "-", "→": "->", "•": "-", "…": "...", " ": " "}.items():
        text = text.replace(k, v)
    text = text.encode("latin-1", "ignore").decode("latin-1")
    # break very long unbroken strings (URLs) so the PDF can wrap them
    return re.sub(r"(\S{90})(?=\S)", r"\1 ", text)


def cmd_pdf(a):
    from fpdf import FPDF

    md = sys.stdin.read().strip()
    if not md:
        sys.exit("Pipe the markdown into stdin.")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_title(a.title)

    def line(txt, size=11, style="", indent=0, font="Helvetica", h=6):
        pdf.set_font(font, style, size)
        pdf.set_x(pdf.l_margin + indent)
        pdf.multi_cell(0, h, _latin(txt), new_x="LMARGIN", new_y="NEXT")

    code = False
    for raw in md.splitlines():
        s = raw.rstrip()
        if s.startswith("```"):
            code = not code
            continue
        if code:
            line(s or " ", 9, font="Courier", h=5)
            continue
        s = s.replace("**", "").replace("`", "")
        if s.startswith("# "):
            pdf.ln(2); line(s[2:], 18, "B", h=9); pdf.ln(1)
        elif s.startswith("## "):
            pdf.ln(3); line(s[3:], 14, "B", h=8)
        elif s.startswith("### "):
            pdf.ln(2); line(s[4:], 12, "B", h=7)
        elif re.match(r"\s*[-*] ", s):
            n = len(s) - len(s.lstrip())
            line("- " + s.strip()[2:], indent=4 + n * 2)
        elif s.startswith("> "):
            line(s[2:], style="I", indent=4)
        elif not s.strip():
            pdf.ln(2)
        else:
            line(s)
    out_dir = cdir(a.course)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{safe(a.title)}.pdf"
    pdf.output(str(out))
    print(out)


def cmd_dedupe(a):
    """Final check: find exact duplicate files anywhere in the course folder. --delete removes the extras."""
    import hashlib

    root = cdir(a.course)
    groups = {}
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        groups.setdefault(hashlib.sha256(f.read_bytes()).hexdigest(), []).append(f)
    extra = [f for g in groups.values() if len(g) > 1 for f in g[1:]]
    for g in groups.values():
        if len(g) > 1:
            print(f"keep {g[0].relative_to(root)}; duplicate: " + ", ".join(str(f.relative_to(root)) for f in g[1:]))
    if a.delete:
        for f in extra:
            f.unlink()
    print(f"{len(extra)} duplicate files " + ("deleted" if a.delete else "found (run again with --delete to remove)")
          + f" in {root}")


def cmd_merge(a):
    """Join PDFs from a folder into ONE PDF named after the course. Exact duplicates are skipped."""
    import hashlib

    from pypdf import PdfReader, PdfWriter

    def natural(p):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]

    files = sorted(pathlib.Path(a.folder).expanduser().glob(a.glob), key=natural)
    if not files:
        sys.exit(f"No files match {a.glob} in {a.folder}")
    w, seen, used, dupes = PdfWriter(), set(), [], []
    for f in files:
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if digest in seen:
            dupes.append(f)
            continue
        seen.add(digest)
        try:
            pages = PdfReader(str(f)).pages
        except Exception as e:
            print(f"skipped unreadable {f.name}: {e}", file=sys.stderr)
            continue
        start = len(w.pages)
        for pg in pages:
            w.add_page(pg)
        w.add_outline_item(f.stem, start)  # bookmark per source file
        used.append(f)
    out_dir = cdir(a.course)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{safe(a.name) if a.name else out_dir.name}.pdf"
    with open(out, "wb") as fh:
        w.write(fh)
    if a.delete_dupes:
        for d in dupes:
            d.unlink()
    if a.delete_sources:
        for f in used + dupes:
            if f.exists():
                f.unlink()
    print(out)
    print(f"{len(used)} files merged, {len(dupes)} exact duplicates skipped"
          + (" and deleted" if a.delete_dupes or a.delete_sources else "")
          + (", sources deleted" if a.delete_sources else "") + f". {len(w.pages)} pages.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **kw):
        p = sp.add_parser(name, **kw)
        p.add_argument("--course", required=True)
        p.set_defaults(fn=fn)
        return p

    p = add("shot", cmd_shot, help="screenshot into the vault")
    p.add_argument("--label", default="shot")
    p.add_argument("--monitor", type=int, default=1, help="0 = all screens")
    p.add_argument("--region", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    p.add_argument("--delay", type=float, default=0)
    p.add_argument("--ocr", action="store_true", help="also write the page text to sources/")

    p = add("dedupe", cmd_dedupe, help="scan the course folder for exact duplicate files")
    p.add_argument("--delete", action="store_true", help="delete the duplicates")

    p = add("merge", cmd_merge, help="merge PDFs from a folder into one PDF named after the course")
    p.add_argument("folder", help="folder holding the downloaded PDFs")
    p.add_argument("--glob", default="*.pdf", help='which files, e.g. "ELEC1111 *.pdf"')
    p.add_argument("--name", help="output file name (default: the course name)")
    p.add_argument("--delete-dupes", action="store_true", help="delete exact duplicate files after merging")
    p.add_argument("--delete-sources", action="store_true", help="delete the single files after merging (ask the user first)")

    p = add("grab", cmd_grab, help="download only: pages, linked files, video captions (no summary, no tokens)")
    p.add_argument("url")
    p.add_argument("--depth", type=int, default=1, help="0 = this page, 1 = plus pages it links to")
    p.add_argument("--max-pages", type=int, default=30)
    p.add_argument("--max-mb", type=int, default=50, help="skip files larger than this")
    p.add_argument("--videos", action="store_true", help="also download captions of YouTube links found")
    p.add_argument("--pace", type=int, default=25, help="seconds to wait between videos (avoids HTTP 429)")

    p = add("fixcaptions", cmd_fixcaptions, help="auto-correct a transcript using the course's own terms")
    p.add_argument("file")
    p.add_argument("--terms", help="extra terms file, one per line")
    p.add_argument("--fix-at", dest="fix_at", type=float, default=0.88, help="similarity to fix silently")
    p.add_argument("--flag-at", dest="flag_at", type=float, default=0.78, help="similarity to mark [ambiguous]")

    p = add("webshot", cmd_webshot, help="picture of a web page (headless browser, page only)")
    p.add_argument("url")
    p.add_argument("--label", default="page")
    p.add_argument("--width", type=int, default=1200)
    p.add_argument("--height", type=int, default=4000)

    p = add("ocr", cmd_ocr, help="read text from an existing image")
    p.add_argument("file")

    p = add("transcribe", cmd_transcribe, help="audio/video file to transcript")
    p.add_argument("file")
    p.add_argument("--model", default="small")

    p = add("record", cmd_record, help="record mic until Ctrl+C, then transcribe")
    p.add_argument("--model", default="small")

    p = add("slides", cmd_slides, help="extract text from pdf/pptx/txt")
    p.add_argument("file")

    p = add("note", cmd_note, help="save markdown from stdin as a note")
    p.add_argument("--title", required=True)
    p.add_argument("--kind", choices=["lecture", "homework"], default="lecture")

    p = add("save", cmd_save, help="save text from stdin into sources/ (for pages read in a browser)")
    p.add_argument("--label", default="page")
    p.add_argument("--source", default="", help="URL the text came from")

    p = add("fetch", cmd_fetch, help="download a public web page (and same-site links) as text")
    p.add_argument("url")
    p.add_argument("--depth", type=int, default=0, help="0 = this page only, 1 = plus pages it links to")
    p.add_argument("--max-pages", type=int, default=10)

    p = add("captions", cmd_captions, help="YouTube/video URL to transcript (captions, else audio)")
    p.add_argument("url")
    p.add_argument("--lang", default="en")
    p.add_argument("--captions-only", action="store_true", help="never fall back to audio download")
    p.add_argument("--retries", type=int, default=3, help="tries when YouTube rate-limits")
    p.add_argument("--model", default="small")

    p = add("pdf", cmd_pdf, help="markdown on stdin to a PDF in <vault>/<course>/")
    p.add_argument("--title", required=True)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
