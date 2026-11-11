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


SECTIONS = {"sources": "_work", "lectures": "_work", "notes": "_work",
            "attachments": "Homework", "homework": "Homework"}


def cdir(course):
    """The one folder for a course, like 'ELEC1111 Vault'. It ends with three PDFs
    (Slides, Notes, Exam Prep) plus an optional Homework folder. '_work' holds temporary files."""
    name = safe(course)
    if not name.lower().endswith("vault"):
        name += " Vault"
    root = vault() / name
    for part in ("Homework", "Assignments"):  # folders: Homework holds pictures, Assignments holds plans
        (root / part).mkdir(parents=True, exist_ok=True)
    return root


def stamp():
    return dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def sub(course, name, group=None):
    d = cdir(course) / SECTIONS.get(name, name)
    if group:  # subfolder such as 'Week 3'
        d = d / safe(group)
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_shot(a):
    import mss
    import mss.tools

    if a.delay:
        time.sleep(a.delay)
    out = sub(a.course, "attachments", a.group) / f"{stamp()}-{slug(a.label)}.png"
    with mss.mss() as s:
        area = s.monitors[a.monitor]
        if a.region:
            x, y, w, h = a.region
            area = {"left": x, "top": y, "width": w, "height": h}
        img = s.grab(area)
        mss.tools.to_png(img.rgb, img.size, output=str(out))
    print(out)
    print(f"![[{out.name}]]")


def _ocr(image, course, region=None):
    """Read text from an image, or only from a region (the question itself).
    Appends to <course> Vault/2 Homework/Questions.md, so whole pages are never stored as text."""
    import numpy as np
    from PIL import Image
    from rapidocr_onnxruntime import RapidOCR

    img = Image.open(image).convert("RGB")
    if region:
        x, y, w, h = region
        img = img.crop((x, y, x + w, y + h))
    result, _ = RapidOCR()(np.array(img))
    text = "\n".join(r[1] for r in (result or []))
    root = sub(course, "attachments")
    out = root / "Questions.md"
    try:  # name the question by its folder and file, for example "Week 3/q12.png"
        label = pathlib.Path(image).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        label = pathlib.Path(image).name
    with open(out, "a", encoding="utf-8") as f:
        f.write(f"## {label}\n\n{text}\n\n")
    return out


def cmd_ocr(a):
    print(_ocr(a.file, a.course, a.region))


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
    body = sys.stdin.buffer.read().decode("utf-8", errors="replace").strip()
    if not body:
        sys.exit("Pipe the markdown note into stdin.")
    d = sub(a.course, "notes")
    out = d / f"{dt.date.today()}-{a.kind}-{slug(a.title)}.md"
    head = f"---\ncourse: {a.course}\nkind: {a.kind}\ndate: {dt.date.today()}\n---\n\n"
    out.write_text(head + body + "\n", encoding="utf-8")
    print(out)


def cmd_save(a):
    text = sys.stdin.buffer.read().decode("utf-8", errors="replace").strip()
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

    src = sub(a.course, "sources")
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
    fdir = sub(a.course, "sources") / "files"
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

    idx = sub(a.course, "sources") / "index.md"
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
    out = sub(a.course, "attachments", a.group) / f"{stamp()}-{slug(a.label)}.png"
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


UNICODE_FONT = {"on": False}


def _unicode_fonts():
    """Regular, bold and italic TrueType fonts that hold Greek letters and maths symbols, or None."""
    sets = [("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/ariali.ttf"),
            ("/Library/Fonts/Arial Unicode.ttf",) * 3,
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf")]
    return next((s for s in sets if all(os.path.exists(p) for p in s)), None)


def _plain(text):
    """Swap typographic quotes and bullets. With only the core PDF fonts (latin-1), turn
    common maths symbols into plain words and drop the rest."""
    for k, v in {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-",
                 "—": "-", "•": "-", "…": "...", chr(160): " "}.items():
        text = text.replace(k, v)
    if UNICODE_FONT["on"]:
        # common TrueType fonts lack sub/superscripts and the angle sign: write them as plain text
        sub_map = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-"))
        sup_map = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-"))
        text = "".join(sub_map.get(c, c) for c in text)

        def _sup(m):
            run = m.group(0)
            return run if all(c in "¹²³" for c in run) else "^" + "".join(sup_map[c] for c in run)

        text = re.sub("[" + "".join(sup_map) + "]+", _sup, text)
        return text.replace("∠", " angle ")
    for k, v in {"→": "->", "Ω": "ohm", "τ": "tau", "ω": "omega", "π": "pi",
                 "∠": "angle ", "Δ": "Delta", "Σ": "sum", "≈": "~", "≤": "<=",
                 "≥": ">=", "∞": "inf", "√": "sqrt", "θ": "theta", "φ": "phi",
                 "μ": "u", "∫": "int", "≠": "!=", "−": "-"}.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "ignore").decode("latin-1")


def _latin(text):
    # break very long unbroken strings so the PDF can wrap them
    return re.sub(r"(\S{90})(?=\S)", r"\1 ", _plain(text))


def cmd_pdf(a):
    from fpdf import FPDF

    md = sys.stdin.buffer.read().decode("utf-8", errors="replace").strip()
    if not md:
        sys.exit("Pipe the markdown into stdin.")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    family = "Helvetica"
    fonts = _unicode_fonts()
    if fonts:  # a real font shows Greek letters, ohm, infinity and similar symbols
        for style, path in zip(("", "B", "I"), fonts):
            pdf.add_font("Body", style, path)
        family = "Body"
        UNICODE_FONT["on"] = True
    pdf.add_page()
    pdf.set_title(a.title)

    link_re = re.compile(r"(\[[^\]]+\]\(https?://[^)\s]+\)|https?://[^\s)]+)")

    def line(txt, size=11, style="", indent=0, font=None, h=6):
        font = font or family
        pdf.set_font(font, style, size)
        pdf.set_x(pdf.l_margin + indent)
        if font == "Courier" or not link_re.search(txt):
            pdf.multi_cell(0, h, _latin(txt), new_x="LMARGIN", new_y="NEXT")
            return
        for part in link_re.split(txt):  # clickable links: [label](url) and bare urls
            if not part:
                continue
            m = re.match(r"\[([^\]]+)\]\((.+)\)$", part)
            if m or part.startswith("http"):
                label, url = (m.group(1), m.group(2)) if m else (part, part)
                pdf.set_text_color(0, 0, 200)
                pdf.set_font(font, "U", size)
                pdf.write(h, _plain(label), link=url)
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font(font, style, size)
                pdf.write(h, _plain(part))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(h)

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
        elif re.fullmatch(r"-{3,}", s.strip()):  # markdown rule: a thin line, not the dashes as text
            pdf.ln(1)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
        elif not s.strip():
            pdf.ln(2)
        else:
            line(s)
    dest = cdir(a.course) / "Assignments" if a.section == "assignment" else cdir(a.course)
    out = dest / f"{safe(a.title)}.pdf"
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
    base = re.sub(r" Vault$", "", cdir(a.course).name)
    out = cdir(a.course) / f"{safe(a.name) if a.name else base + ' Slides'}.pdf"
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


def _question_pictures(pdf, scale, colors, keep_chrome):
    """Yield one picture per page, cropped to the question content only. Headers, footers, logos,
    page numbers and watermarks are dropped: objects in the top or bottom band that repeat on other
    pages (or any object in the band of a single-page file), and page-sized background objects."""
    n = len(pdf)
    top_band, bottom_band = 0.115, 0.075
    pages = []
    for i in range(n):
        page = pdf[i]
        w, h = page.get_size()
        objs = []
        for obj in page.get_objects(max_depth=1):
            l, b, r, t = obj.get_bounds()
            key = (obj.type, round(l / 6), round(b / 6), round(r / 6), round(t / 6))
            objs.append((key, (l, b, r, t)))
        pages.append((page, w, h, objs))
    seen = {}
    for _, _, _, objs in pages:
        for key, _ in objs:
            seen[key] = seen.get(key, 0) + 1
    for page, w, h, objs in pages:
        keep = []
        for key, (l, b, r, t) in objs:
            in_band = b > h * (1 - top_band) or t < h * bottom_band  # wholly inside the header or footer strip
            repeated = True
            background = (r - l) * (t - b) > 0.85 * w * h
            watermark = (r - l) * (t - b) > 0.5 * w * h and seen[key] >= 2
            if not keep_chrome and (background or watermark or in_band):
                continue
            keep.append((l, b, r, t))
        img = page.render(scale=scale).to_pil().convert("RGB")
        if keep:
            pad = 8
            l = max(0, min(k[0] for k in keep) - pad)
            r = min(w, max(k[2] for k in keep) + pad)
            b = max(0, min(k[1] for k in keep) - pad)
            t = min(h, max(k[3] for k in keep) + pad)
            img = img.crop((int(l * scale), int((h - t) * scale), int(r * scale), int((h - b) * scale)))
        if colors:
            img = img.quantize(colors=colors)
        yield img


def cmd_pdfpics(a):
    """Turn each page of a homework PDF into a picture in Homework/<group>/. The questions are the
    PDF's own text (no OCR needed for text PDFs), saved to Homework/Questions.md."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(a.file)
    label = safe(a.label or pathlib.Path(a.file).stem)
    d = sub(a.course, "attachments", a.group)
    for i, img in enumerate(_question_pictures(pdf, a.scale, a.colors, a.keep_chrome)):
        img.save(d / f"{label} p{i + 1:02d}.png", optimize=True)
    if not a.no_text:
        from pypdf import PdfReader

        text = "\n".join((p.extract_text() or "") for p in PdfReader(a.file).pages).strip()
        title = f"{a.group}/{label}" if a.group else label
        with open(sub(a.course, "attachments") / "Questions.md", "a", encoding="utf-8") as f:
            f.write(f"## {title}\n\n{text}\n\n")
    print(f"{label}: {len(pdf)} pictures in {d.relative_to(cdir(a.course)).as_posix()}")


def cmd_slidepics(a):
    """Pictures of the practice problems in lecture slides: the question text and the circuit only.
    Finds slides titled 'Example n' or 'Practice problem n', then drops the title, the worked-solution
    note, the answer box, the page number and the logo. Question text goes to Homework/Questions.md."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(a.file)
    groups = []
    for part in (a.groups or "").split(";"):
        if "=" in part:
            name, rng = part.split("=")
            lo, hi = rng.split("-")
            groups.append((name.strip(), int(lo), int(hi)))
    title_re = re.compile(r"^\s*((?:Example|Practice problem)\s*\d+)\s*$", re.I)
    qfile = sub(a.course, "attachments") / "Questions.md"
    count = 0
    for n in range(len(pdf)):
        page = pdf[n]
        w, h = page.get_size()
        tp = page.get_textpage()
        lines = [x.strip() for x in tp.get_text_range().splitlines() if x.strip()]
        if not lines or not title_re.match(lines[0]) or "solution" in lines[0].lower():
            continue
        title = re.sub(r"\s+", " ", title_re.match(lines[0]).group(1)).strip().capitalize()
        objs = [(o, o.get_bounds()) for o in page.get_objects(max_depth=1)]
        drop = set()

        def box_of(word):
            hit = tp.search(word).get_next()
            return tp.get_charbox(hit[0]) if hit else None

        for i, (o, (l, b, r, t)) in enumerate(objs):
            if (r - l) * (t - b) > 0.85 * w * h or b > h * 0.87:  # background, slide title
                drop.add(i)
            if l > w * 0.85 and t < h * 0.16:  # logo and page number in the bottom-right corner
                drop.add(i)
        ans = box_of("Answer")
        if ans:  # the box that holds the answer, and everything inside it
            holders = [bd for i, (o, bd) in enumerate(objs)
                       if o.type == 2 and i not in drop and bd[0] <= ans[0] + 2 and bd[1] <= ans[1] + 2
                       and bd[2] >= ans[2] - 2 and bd[3] >= ans[3] - 2 and (bd[2] - bd[0]) * (bd[3] - bd[1]) < 0.6 * w * h]
            area = min(holders, key=lambda bd: (bd[2] - bd[0]) * (bd[3] - bd[1])) if holders else (ans[0] - 4, 0, w, ans[3] + 4)
            for i, (o, (l, b, r, t)) in enumerate(objs):
                if l >= area[0] - 3 and b >= area[1] - 3 and r <= area[2] + 3 and t <= area[3] + 3:
                    drop.add(i)
        note = box_of("Worked solutions")  # painted over below, because it shares a text object with the question
        keep = [bd for i, (o, bd) in enumerate(objs) if i not in drop]
        if not keep:
            continue
        pad = 10
        l = max(0, min(k[0] for k in keep) - pad)
        r = min(w, max(k[2] for k in keep) + pad)
        b = max(0, min(k[1] for k in keep) - pad)
        t = min(h, max(k[3] for k in keep) + pad)
        img = page.render(scale=a.scale).to_pil().convert("RGB")
        if note:  # white out the "(Worked solutions of examples ...)" line, but not any figure on the same rows
            from PIL import ImageDraw

            y0, y1 = note[1] - 3, note[3] + 3
            x_end = w
            for k, (o, (ol, ob, orr, ot)) in enumerate(objs):
                if o.type != 1 and k not in drop and ob < y1 and ot > y0 and orr - ol < 0.85 * w:
                    x_end = min(x_end, ol - 2)
            ImageDraw.Draw(img).rectangle([0, int((h - y1) * a.scale), int(x_end * a.scale), int((h - y0) * a.scale)], fill="white")
        img = img.crop((int(l * a.scale), int((h - t) * a.scale), int(r * a.scale), int((h - b) * a.scale)))
        if a.colors:
            img = img.quantize(colors=a.colors)
        group = next((g[0] for g in groups if g[1] <= n + 1 <= g[2]), None)
        d = sub(a.course, "attachments", "Slides")
        if group:
            d = d / safe(group)
            d.mkdir(parents=True, exist_ok=True)
        img.save(d / f"{title} (Slides p. {n + 1}).png", optimize=True)
        text = re.sub(r"\s+", " ", tp.get_text_bounded(l, b, r, t)).strip()
        text = re.sub(r"\(Worked solutions.*?\)", "", text).strip()
        with open(qfile, "a", encoding="utf-8") as f:
            f.write(f"## Slides/{group + '/' if group else ''}{title} (Slides p. {n + 1})\n\n{text}\n\n")
        count += 1
    print(f"{count} slide questions saved as pictures in Homework/Slides")


def cmd_cleanpics(a):
    """Re-crop pictures already in Homework/: drop the header and footer strips (logos, page numbers)
    and the white margins, and limit the colours. Changes the files in place. Run it once per picture."""
    from PIL import Image, ImageChops

    root = sub(a.course, "attachments")
    done = 0
    before = after = 0
    for p in sorted(root.rglob("*.png")):
        if any(skip in p.relative_to(root).parts for skip in (a.skip or [])):
            continue
        if a.only and a.only not in p.relative_to(root).as_posix():
            continue
        before += p.stat().st_size
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.crop((0, int(h * a.top), w, h - int(h * a.bottom)))
        dark = ImageChops.invert(im.convert("L")).point(lambda v: 255 if v > 40 else 0)
        for y in range(min(60, dark.height)):  # a wide line near the top is the header rule: cut it and what is above it
            row = dark.crop((0, y, dark.width, y + 1)).histogram()[255]
            if row > 0.75 * dark.width:
                im = im.crop((0, y + 2, im.width, im.height))
                dark = dark.crop((0, y + 2, dark.width, dark.height))
                break
        ink = dark.getbbox()
        if ink:
            pad = 8
            im = im.crop((max(0, ink[0] - pad), max(0, ink[1] - pad), min(im.width, ink[2] + pad), min(im.height, ink[3] + pad)))
        if a.colors:
            im = im.quantize(colors=a.colors)
        im.save(p, optimize=True)
        after += p.stat().st_size
        done += 1
    print(f"{done} pictures re-cropped, {before // 1024} KB -> {after // 1024} KB")


def cmd_receive(a):
    """Run a small server on this PC (127.0.0.1 only). A logged-in browser page sends files and
    screenshots to it, one at a time, and they land in the vault. Needs the printed token."""
    import secrets
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    token = a.token or secrets.token_hex(8)
    state = {"last": time.time(), "count": 0}

    class Handler(BaseHTTPRequestHandler):
        timeout = 20  # drop idle or half-open connections (browsers open spare ones)

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Private-Network", "true")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_POST(self):
            q = parse_qs(urlparse(self.path).query)
            if q.get("token", [""])[0] != token:
                self.send_response(403)
                self._cors()
                self.end_headers()
                return
            kind = q.get("kind", ["file"])[0]
            name = safe(q.get("name", ["file"])[0]).lstrip(".") or "file"
            group = (q.get("group", [""])[0] or "").strip().strip(".") or None
            data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            dest = sub(a.course, "attachments" if kind == "shot" else "sources", group) / name
            dest.write_bytes(data)
            state["last"] = time.time()
            state["count"] += 1
            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(b"ok")
            print(f"saved {dest.relative_to(cdir(a.course)).as_posix()} ({len(data) // 1024} KB)", flush=True)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    server.timeout = 2
    print(f"receiver ready: port {a.port} token {token} (stops after {a.idle}s with no uploads)", flush=True)
    while time.time() - state["last"] < a.idle:
        server.handle_request()
    print(f"receiver stopped after {state['count']} uploads", flush=True)


def cmd_finish(a):
    """Last step: remove duplicates, then delete every working file used to build the vault."""
    import shutil

    root = cdir(a.course)
    cmd_dedupe(argparse.Namespace(course=a.course, delete=True))
    work = root / "_work"
    if work.exists() and not a.keep_work:
        shutil.rmtree(work)
        print("deleted working files: _work")
    for f in a.also_delete or []:
        p = pathlib.Path(f).expanduser()
        if p.is_file():
            p.unlink()
            print(f"deleted: {p}")
        else:
            print(f"skipped (not a file): {p}", file=sys.stderr)
    print("Vault now holds:")
    for p in sorted(root.iterdir()):
        if p.is_dir():
            print(f"  {p.name}/ ({sum(1 for f in p.rglob('*') if f.is_file())} files)")
        else:
            print("  " + p.name)


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
    p.add_argument("--group", help="subfolder in Homework, for example Week 3")
    p.add_argument("--monitor", type=int, default=1, help="0 = all screens")
    p.add_argument("--region", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    p.add_argument("--delay", type=float, default=0)

    p = add("pdfpics", cmd_pdfpics, help="pages of a homework PDF into pictures in Homework/<group>/, plus the question text")
    p.add_argument("file")
    p.add_argument("--group", help="subfolder, for example 'Week 3'")
    p.add_argument("--label", help="picture name prefix (default: the file name)")
    p.add_argument("--scale", type=float, default=1.4, help="picture size, 1.0 = 72 dpi")
    p.add_argument("--no-text", action="store_true", help="do not add the text to Questions.md (for solutions)")
    p.add_argument("--colors", type=int, default=64, help="limit the picture to this many colours to save space (0 = off)")
    p.add_argument("--keep-chrome", action="store_true", help="keep headers, footers, logos and watermarks")

    p = add("slidepics", cmd_slidepics, help="pictures of the Example and Practice problems in lecture slides (question and circuit only)")
    p.add_argument("file", help="the merged slides PDF (or any slides PDF)")
    p.add_argument("--groups", help='slide ranges by topic, for example "Topic 1=1-62;Topic 2=63-122"')
    p.add_argument("--scale", type=float, default=1.6)
    p.add_argument("--colors", type=int, default=64)

    p = add("cleanpics", cmd_cleanpics, help="re-crop pictures already in Homework/ (no logos, headers, footers, margins)")
    p.add_argument("--top", type=float, default=0.115, help="share of the height to cut from the top")
    p.add_argument("--bottom", type=float, default=0.075, help="share of the height to cut from the bottom")
    p.add_argument("--colors", type=int, default=64)
    p.add_argument("--skip", nargs="*", metavar="FOLDER", help="subfolders to leave alone, for example Quizzes")
    p.add_argument("--only", help="only pictures whose path contains this text")

    p = add("receive", cmd_receive, help="local server: a logged-in browser page sends files and pictures into the vault")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--idle", type=int, default=900, help="stop after this many seconds with no uploads")
    p.add_argument("--token", help="secret the page must send (default: random, printed at start)")

    p = add("finish", cmd_finish, help="last step: dedupe, then delete all working files used to build the vault")
    p.add_argument("--also-delete", nargs="*", metavar="FILE", help="files this run downloaded elsewhere (for example in Downloads)")
    p.add_argument("--keep-work", action="store_true", help="keep the _work folder")

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
    p.add_argument("--group", help="subfolder in Homework, for example Week 3")
    p.add_argument("--width", type=int, default=1200)
    p.add_argument("--height", type=int, default=4000)

    p = add("ocr", cmd_ocr, help="OCR only the question region of an image into 2 Homework/Questions.md")
    p.add_argument("file")
    p.add_argument("--region", type=int, nargs=4, metavar=("X", "Y", "W", "H"), help="only this rectangle (the question)")

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

    p = add("pdf", cmd_pdf, help="markdown on stdin to a PDF in one of the three parts")
    p.add_argument("--title", required=True)
    p.add_argument("--section", choices=["notes", "exam", "assignment"], default="notes",
                   help="notes and exam go in the vault root; assignment goes in Assignments/. The file is named by --title")

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
