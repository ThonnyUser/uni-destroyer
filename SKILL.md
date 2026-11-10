---
name: homework-vault
description: Turn a lecture page, URL, recording, slides, or screenshot into a summary note in a local vault, file homework with tips, and suggest videos to watch. Use when the user gives a course URL or opens a course page, wants a lecture summarised, wants homework captured, or asks to file study material.
---

# Homework Vault

Work runs locally. `scripts/hw.py` gathers material. **You** read it and write the whole summary yourself. Do not call any other summariser.

## Setup (once)

```bash
pip install rapidocr-onnxruntime mss trafilatura lxml_html_clean yt-dlp faster-whisper sounddevice numpy pypdf python-pptx
export HW_VAULT="/path/to/your/vault"   # Windows PowerShell: $env:HW_VAULT = "C:\path\to\vault"
```

Install only what the task needs. If `HW_VAULT` is not set, ask the user for the path. Never guess it.

## Commands

All need `--course <name>`. Files go to `$HW_VAULT/<course>/`. Each prints the path it wrote.

| Job | Command |
|---|---|
| Download a public page | `python scripts/hw.py fetch URL --course C` (`--depth 1` also takes same-site links) |
| Save text you read in a browser | `python scripts/hw.py save --course C --label L --source URL` with text on stdin |
| Video link to transcript | `python scripts/hw.py captions URL --course C` (captions, else audio) |
| Screenshot | `python scripts/hw.py shot --course C --label L [--ocr] [--region X Y W H] [--delay 3]` |
| OCR an image | `python scripts/hw.py ocr page.png --course C` |
| Transcribe a recording | `python scripts/hw.py transcribe file.mp4 --course C` |
| Record live audio | `python scripts/hw.py record --course C` (Ctrl+C stops) |
| Read slides | `python scripts/hw.py slides deck.pdf --course C` (pdf, pptx, txt) |
| Save a note | `python scripts/hw.py note --course C --title T --kind lecture` with markdown on stdin |

## Workflow: user gives a URL or has a page open

1. **Page open in the user's browser** (course site, LMS, anything behind a login): use your browser tool, not `fetch`. Read the page text and the list of links. Save each page with `save`. Then open the relevant linked pages (lectures, readings, assignments) one by one, up to about 10, and save each. Stay on the same site. Stop and ask before opening more than 10.
2. **Public URL, nothing open**: run `fetch`. Add `--depth 1` if the user wants the linked pages too. If it reports "no text", the page needs a login or JavaScript: ask the user to open it in their browser and go to step 1.
3. **Video link** (YouTube etc.): run `captions`.
4. Read every saved file. Write the lecture note (below). Put homework found on the pages into homework notes (below).

## Workflow: lecture note

Write in markdown, then pipe to `note --kind lecture`:

- one-paragraph overview
- key concepts, each with a short plain explanation
- definitions and formulas, exact as the source states them
- open questions or unclear points
- **Watch next**: 3 to 6 video suggestions (below)

For recordings and live audio, keep `[mm:ss]` markers on important points.

## Watch next (video suggestions)

Suggest videos by **title and channel only**. Never watch or transcribe them. Use your web search to find real titles from well-known educational channels (for example 3Blue1Brown, Khan Academy, CrashCourse, MIT OpenCourseWare, Professor Leonard, StatQuest, Organic Chemistry Tutor, Computerphile). Add the URL only if your search returned it. Never invent a URL or a title. If you cannot search, list topics to look up instead.

## Workflow: homework

1. Get the assignment: `shot --ocr`, a browser read, or `fetch`. Look at images yourself; OCR can mangle formulas and tables.
2. Save a `homework` note with: the task in your own words, due date and marks if visible, the rubric if present, and `![[file.png]]` embeds from `shot`.
3. Add **Tips**, tailored to the task. Cover what applies:
   - break the task into steps with a rough time for each
   - what the marker is likely to reward (read the rubric)
   - which lecture notes and readings in the vault apply, linked by file name
   - a starting outline or structure
   - common mistakes for this kind of task
   - questions worth asking the lecturer or tutor, and office hours or study groups
   - tools that fit: calculators, code editors, reference managers, past worked examples
4. If the user asks you to solve it or draft it, do so. Show your working so they can learn from it and check it.

## Dictation (Wispr Flow or any voice-to-text app)

Dictation apps type into the focused window, so it reaches you as ordinary text. Treat dictated remarks as the user's own notes. Add them word for word under `## My notes`.

## Rules

- Take a screenshot only when the user asks. Say what area was captured.
- Write only inside `$HW_VAULT`.
- If something is unreadable in an image, audio, or page, say so. Do not invent it.
- Keep exact numbers, names, and formulas from the source.
