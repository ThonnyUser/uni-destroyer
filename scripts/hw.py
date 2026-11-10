#!/usr/bin/env python3
"""hw.py - local helper for the homework-vault skill.

Gathers material only. The calling LLM reads it and writes the summary.
Vault path comes from the HW_VAULT environment variable.
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
    if not v:
        sys.exit("Set HW_VAULT to your vault folder first.")
    p = pathlib.Path(v).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def slug(s):
    return re.sub(r"[^\w\-]+", "-", s.strip()).strip("-").lower() or "untitled"


def stamp():
    return dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def sub(course, name):
    d = vault() / slug(course) / name
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

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
