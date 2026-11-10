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

**Download only.** If the user wants the material downloaded without summaries, run `python scripts/hw.py grab URL --course C --depth 1 --videos` and stop. Do not read the files and do not summarise. Tell the user where the files are (`index.md` lists everything). This costs almost no tokens. Pages behind a login need your browser tool instead.

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
| Download a whole site (no summary) | `python scripts/hw.py grab URL --course C --depth 1 --videos` |
| Download a public page | `python scripts/hw.py fetch URL --course C` (`--depth 1` adds same-site links) |
| Save text you read in a browser | `python scripts/hw.py save --course C --label L --source URL` with text on stdin |
| Video link to transcript | `python scripts/hw.py captions URL --course C --captions-only` |
| Auto-correct a transcript | `python scripts/hw.py fixcaptions transcript.txt --course C` (writes `.corrected.txt` and `.corrections.txt`) |
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

1. **Page open in the user's browser** (login pages, JavaScript pages): use your browser tool. Read the page text and the list of links. Course pages often hide lecture links in a side menu that `fetch` misses, so list all links with a script (for example, every link whose text contains "YouTube", "Lecture", "Slides", "Week"). Then run `scripts/expand.js` in the page, twice, to open every hidden section: accordions, tabs, "Show more", collapsed examples and code. Check that the text length goes up. The script clicks only closed toggles. It never clicks submit, delete, post, pay, send, save, or sign-out buttons, and you must not click those either.
2. **Public page**: run `fetch`. Add `--depth 1` for linked pages. If it reports "no text", use your browser tool.
3. **Crawl the whole site.** If the user wants everything, cover every week and every lecture. Do not stop at a sample. Open every link on the same site that holds course material: weekly pages, lectures, tutorials, labs, assignments, resources, FAQ. Run `expand.js` on each page first. Keep a list of visited URLs so you never loop. Stay on the course site, and do not open links to other sites unless they are lecture videos or the user asks.
4. **Lecture videos**: run `captions URL --captions-only` for each. Pace them, and expect "HTTP 429 Too Many Requests" from YouTube. The script retries with waits. For videos that still fail, run again later, or transcribe the audio with `faster-whisper` if the user allows the large download.
5. Correct each transcript (next section), then read it and the slides. Write the summaries.

## Workflow: correcting transcripts

Auto-captions mishear technical words ("print f", "maloc", "strruct"). Fix them in two steps. Never fix silently where you are unsure.

1. **Run `fixcaptions`** on each transcript, after `fetch` or `save` has stored the course pages. It uses the course's own vocabulary (code names from the pages, plus common programming terms) to fix clear mishearings and to join split words like "scan f" into `scanf`. Unsure cases are marked `[ambiguous: maybe X]` in the text. It keeps the original file and writes a log of every change. Read the log: undo any change that looks wrong. `--terms file.txt` adds extra words, one per line.
2. **Correct by context while you read.** Use the slides, code pages and assignment text to fix names, spellings and obvious errors. Check every number, formula and line of code against a source.
3. **If you cannot correct it with confidence, write `[ambiguous]`** (or `[ambiguous: could be X or Y]`) in the notes. Never guess a number, formula, name or code. Never drop a doubtful passage without saying so.
4. End the notes PDF with a short **Ambiguities** list of everything marked, so the student can check it with the lecturer or the video.

## Workflow: past assignments

When the course site links earlier assignments (or earlier terms of the same course), analyse them too. Open each with your browser tool, run `expand.js`, read it fully, then write one **Past assignments** section in the notes PDF:

- what each assignment asked, and its stages
- how marks were split (performance, style, stages) and the late penalty
- which lecture topics each one tests
- patterns that repeat: typical stage order, rules that cost marks, tools provided
- how the current assignment compares, and what the student can learn from the past ones

Analyse the specs only. Do not collect other students' solutions, and never copy or reuse another person's assignment work.

## Workflow: notes PDF (lecture summaries)

Write markdown, then pipe it to `pdf --title "<course> lecture notes"`. For each lecture:

- one-paragraph overview
- key concepts, each with a short plain explanation
- definitions, formulas and code ideas, exact as the lecturer states them
- common confusions or warnings the lecturer gave
- worked examples in one or two lines

End with **Watch next**: 3 to 6 video suggestions by **title and channel only** from well-known educational channels (for example 3Blue1Brown, Khan Academy, CrashCourse, MIT OpenCourseWare, Professor Leonard, StatQuest). Use web search for real titles. Add a URL only if the search returned it. Never invent a title or URL. Never watch the videos. If you cannot search, list topics to search for.

## Cost warning (tell the user before a big run)

This skill burns a lot of tokens, because you must read the material:

- one lecture transcript: about 12,000 words, roughly 16,000 tokens
- a course with 18 lectures: roughly 300,000 tokens just to read them
- one assignment page with its hidden sections opened: roughly 20,000 tokens
- every extra step re-reads the whole conversation, so real usage is higher

Say this to the user before reading everything, and offer to do one week at a time. A free plan will probably not cover a full course. Work through lectures one at a time and save each summary before moving on.

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
