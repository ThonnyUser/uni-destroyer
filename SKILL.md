---
name: homework-vault
description: Turn a course page, URL, lecture video, recording, slides, or screenshot into a PDF notes document with lecture summaries and concepts, save homework as a picture, and write an assignment plan. Use when the user gives a course URL or has a course page open, wants lectures summarised, wants homework captured, or asks for help planning an assignment.
---

# Homework Vault

Work runs locally. `scripts/hw.py` gathers material. **You** read it and write the whole summary yourself. Do not call any other summariser.

## What the user gets (three outputs)

All outputs go in **Downloads** so the user finds them easily: `~/Downloads/homework-vault/<course>/`. (Set `HW_VAULT` only if the user wants another folder.)

1. **Notes PDF** (`<course>/<title>.pdf`): lecture summaries, key concepts, definitions, formulas, and a "Watch next" list.
2. **Homework picture** (`<course>/attachments/*.png`): an image of the assignment page.
3. **Assignment plan PDF**: advice and a plan only. **Never do the assignment for the user.** No solution code, no answers, no finished drafts. Give a day-by-day schedule, what to review, how the marks work, common mistakes, and where to get help. If the user asks you to solve it, say you only give a plan, and make the plan more detailed.

Working files (transcripts, page text) go in `<course>/sources/` and `<course>/attachments/`. Keep the PDFs at the top of the course folder.

## Setup (once)

1. Install Python 3.12 from https://www.python.org/downloads/ (Windows: tick "Add python.exe to PATH").
2. Install the packages:

```bash
pip install rapidocr-onnxruntime mss trafilatura lxml_html_clean yt-dlp fpdf2 faster-whisper sounddevice numpy pypdf python-pptx
```

Install only what the task needs: `fpdf2` for PDFs, `yt-dlp` for video captions, `trafilatura lxml_html_clean` for `fetch`, `rapidocr-onnxruntime` for OCR, `faster-whisper` only for videos with no captions.

## Commands

All need `--course <name>`. Each prints the path it wrote.

| Job | Command |
|---|---|
| Download a public page | `python scripts/hw.py fetch URL --course C` (`--depth 1` adds same-site links) |
| Save text you read in a browser | `python scripts/hw.py save --course C --label L --source URL` with text on stdin |
| Video link to transcript | `python scripts/hw.py captions URL --course C --captions-only` |
| Picture of a web page (page only) | `python scripts/hw.py webshot URL --course C --label L` (headless Edge or Chrome) |
| Screenshot of the screen | `python scripts/hw.py shot --course C --label L [--ocr] [--region X Y W H] [--delay 3]` |
| OCR an image | `python scripts/hw.py ocr page.png --course C` |
| Transcribe a recording | `python scripts/hw.py transcribe file.mp4 --course C` |
| Record live audio | `python scripts/hw.py record --course C` (Ctrl+C stops) |
| Read slides | `python scripts/hw.py slides deck.pdf --course C` (pdf, pptx, txt) |
| Markdown to PDF | `python scripts/hw.py pdf --course C --title T` with markdown on stdin |
| Save a markdown note | `python scripts/hw.py note --course C --title T --kind lecture` with markdown on stdin |

Prefer `webshot` over `shot` for web pages. `shot` captures the whole desktop and may include private windows.

## Workflow: user gives a course URL, or has a course page open

1. **Page open in the user's browser** (login pages, JavaScript pages): use your browser tool. Read the page text and the list of links. Course pages often hide lecture links in a side menu that `fetch` misses, so list all links with a script (for example, every link whose text contains "YouTube", "Lecture", "Slides", "Week").
2. **Public page**: run `fetch`. Add `--depth 1` for linked pages. If it reports "no text", use your browser tool.
3. **Run all of it.** If the user wants everything, cover every week and every lecture. Do not stop at a sample.
4. **Lecture videos**: run `captions URL --captions-only` for each. Pace them, and expect "HTTP 429 Too Many Requests" from YouTube. The script retries with waits. For videos that still fail, run again later, or transcribe the audio with `faster-whisper` if the user allows the large download.
5. Read the transcripts and slides. Write the summaries.

## Workflow: notes PDF (lecture summaries)

Write markdown, then pipe it to `pdf --title "<course> lecture notes"`. For each lecture:

- one-paragraph overview
- key concepts, each with a short plain explanation
- definitions, formulas and code ideas, exact as the lecturer states them
- common confusions or warnings the lecturer gave
- worked examples in one or two lines

End with **Watch next**: 3 to 6 video suggestions by **title and channel only** from well-known educational channels (for example 3Blue1Brown, Khan Academy, CrashCourse, MIT OpenCourseWare, Professor Leonard, StatQuest). Use web search for real titles. Add a URL only if the search returned it. Never invent a title or URL. Never watch the videos. If you cannot search, list topics to search for.

Transcripts are long (about 12,000 words per lecture). For many lectures, work through them one at a time, and tell the user the cost before reading them all.

## Workflow: homework picture and assignment plan

1. Get the picture: `webshot URL --course C --label assignment-name`. Look at the image. Use `ocr` if you cannot see images.
2. Read the assignment page in full. Note the due date, weight, marks, stages, rules, and any ban on AI help.
3. Write the plan as markdown, then pipe it to `pdf --title "<assignment> plan"`. Include:
   - what the task is, in your own words
   - due date, late penalty, weight, how the marks split
   - the rules, including any ban on AI help, and a reminder to write the work themselves
   - a day-by-day schedule from today to the due date, with stage order and when to submit
   - which lectures and readings to review first
   - habits that save marks: test after each part, submit early and often, style rules from the rubric
   - common mistakes for this kind of task
   - how to get unstuck: help sessions, forum rules, drawing diagrams
4. Do not include solution code or answers.

## Dictation (Wispr Flow or any voice-to-text app)

Dictation apps type into the focused window, so it reaches you as ordinary text. Treat dictated remarks as the user's own notes. Add them word for word under "My notes".

## Rules

- Take a desktop screenshot only when the user asks, and say what was captured.
- Write only inside the output folder.
- If something is unreadable in an image, audio, or page, say so. Do not invent it.
- Keep exact numbers, names, and formulas from the source.
- The user, not this tool, answers for how the material is used. Follow the university's rules.
