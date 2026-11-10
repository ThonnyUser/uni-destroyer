---
name: homework-vault
description: Summarise lectures (recordings, live audio, slides, or what is on screen) and save homework screenshots into a local notes vault. Use when the user wants a lecture summarised, wants a page or assignment captured, or asks to file study material into their vault.
---

# Homework Vault

All work runs locally. The script `scripts/hw.py` gathers material. **You** read it and write the whole summary yourself. Do not call any other summariser.

## Setup (once)

```bash
pip install rapidocr-onnxruntime mss faster-whisper sounddevice numpy pypdf python-pptx
export HW_VAULT="/path/to/your/vault"   # Windows PowerShell: $env:HW_VAULT = "C:\path\to\vault"
```

Install only what the task needs: `mss` for screenshots, `faster-whisper` for transcripts, `sounddevice numpy` for live audio, `pypdf` / `python-pptx` for slides.

If `HW_VAULT` is not set, ask the user for the path. Never guess it.

## Commands

All commands need `--course <name>`. Files go to `$HW_VAULT/<course>/`.

| Job | Command |
|---|---|
| Screenshot the screen | `python scripts/hw.py shot --course C --label topic` |
| Screenshot one area | add `--region X Y W H`; add `--delay 3` to wait first |
| Screenshot plus page text (OCR) | `python scripts/hw.py shot --course C --label topic --ocr` |
| OCR an existing image | `python scripts/hw.py ocr page.png --course C` |
| Transcribe a recording | `python scripts/hw.py transcribe lecture.mp4 --course C` |
| Record live audio | `python scripts/hw.py record --course C` (user presses Ctrl+C to stop) |
| Read slides | `python scripts/hw.py slides deck.pdf --course C` (pdf, pptx, txt) |
| Save a note | `python scripts/hw.py note --course C --title T --kind lecture` with markdown on stdin |

Each command prints the path of the file it wrote.

## Workflow: lecture

1. Gather: run `transcribe`, `record`, or `slides`. If the user points at what is on screen, run `shot` and look at the image.
2. Read every gathered file in full. Combine sources when there is more than one.
3. Write the summary yourself, in markdown:
   - one-paragraph overview
   - key concepts, each with a short plain explanation
   - definitions and formulas, exact as the source states them
   - open questions or unclear points
   - for transcripts, keep `[mm:ss]` markers on important points
4. Save: pipe the markdown to `note --kind lecture`.

## Workflow: homework

1. Run `shot` with `--label` set to the assignment name. Repeat for each page.
2. Look at each image. Read the task text from it.
3. Save a `homework` note with: the task in your own words, the due date if visible, and the embed line(s) the `shot` command printed (`![[file.png]]`).
4. Do **not** solve the homework unless the user asks.

## Dictation (Wispr Flow or any voice-to-text app)

Dictation apps type into the focused window, so their output reaches you as ordinary user text. Treat dictated remarks as the user's own notes: add them to the note under a `## My notes` heading, word for word. The skill needs no setup for this.

## OCR

Use `--ocr` when you cannot view images, or when the page has small text. Read the OCR text file, and check it against the image when both are available. OCR can mangle formulas and tables: say so and trust the image.

## Rules

- Take a screenshot only when the user asks. Tell them what area was captured.
- Write only inside `$HW_VAULT`.
- If something is unreadable in an image or audio, say so. Do not invent it.
- Keep exact numbers, names, and formulas from the source.
