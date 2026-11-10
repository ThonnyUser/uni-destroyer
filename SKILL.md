---
name: homework-vault
description: Build a study vault for one course. Reads every lecture-notes file into one big notes PDF with links, saves screenshots of all homework with OCR of the questions only, and writes an exam and test preparation PDF. Use when the user gives a course URL, has a course page open, or asks for lecture summaries, homework capture, assignment planning or exam preparation.
---

# Homework Vault

Work runs locally. `scripts/hw.py` gathers material. **You** read it and write the summaries yourself. Do not call any other summariser.

## The output: one folder, always three parts

Every course gets one folder named after the course, inside Downloads: `~/Downloads/homework-vault/<COURSE> Vault/` (for example `ELEC1111 Vault`). `hw.py` creates it and these three parts every time (`--course ELEC1111` is enough). Put everything for the course here and nowhere else.

```
<COURSE> Vault/
  1 Notes/         <COURSE> Notes.pdf          the big summary
    Source files/  downloaded lecture notes, page text, transcripts, merged originals
  2 Homework/      screenshots of all homework, Questions.md, assignment plan PDF
  3 Exam Prep/     <COURSE> Exam Prep.pdf
```

### 1 Notes: one big notes PDF
- **Read every single lecture-notes file.** All of them, every page. Do not sample, skip, or stop early. Extract text with `slides` (pdf, pptx), and look at an image only when a diagram carries meaning.
- Summarise all of it into **one** PDF: `pdf --course C --title "<COURSE> Notes" --section notes`. Aim for about 30 pages. Scale with the course: more topics, more pages. Say how long it came out.
- For each topic: overview, key concepts with short plain explanations, definitions and formulas exact as the source states them, worked-example ideas, common mistakes the lecturer warned about.
- **Include links.** Link every topic to its source: the course page, the lecture-notes file name, the lecture recording, the readings, and **Watch next** videos. Write links as `[label](https://...)`. The `pdf` command makes them clickable.
- Use slides and notes first. If a lecture has slides or notes, do **not** transcribe its recording (transcripts are the biggest token cost). Transcribe only lectures that have nothing written.
- Keep the downloaded originals in `1 Notes/Source files/`. `merge` can join them into one PDF there.

### 2 Homework: screenshots, and OCR of the questions only
- Take **one screenshot for every homework page or question**. There may be hundreds. Name each clearly (`--label`), for example `week3-q12`.
- **OCR only the question itself.** Look at the screenshot, find the question's rectangle, then run `ocr FILE --course C --region X Y W H`. This appends the question text to `2 Homework/Questions.md` under the image name. Never OCR a whole page, and never OCR answers, solutions, menus or page chrome. This keeps the text small.
- Also here: the **assignment plan PDF** (`pdf --section homework`). It is advice and a plan only (see below).

### 3 Exam Prep: one preparation PDF
`pdf --course C --title "<COURSE> Exam Prep" --section exam`. Read the course outline, assessments page, quiz and exam pages, past papers, and the notes. Include:
- **When:** every exam, test, quiz and assignment deadline: date, time, room, length, weight, open or closed book, format. Write `[not published]` when you cannot find it. Never invent a date.
- **What each covers:** the topics, from the outline and the notes.
- **What to practice:** question types per topic, which homework and past-paper questions to redo, formulas to memorise, skills to drill.
- **Past papers and solutions:** list and link them.
- **A countdown plan** from today to each exam: what to study each day or week, with time for practice papers.
- Weak spots: topics with the most homework or the hardest questions.
- Short exam-day tips.

## Always: one container, then a duplicate scan

- Everything for a course goes in its one `<COURSE> Vault` folder.
- **At the end of every run, scan for duplicates:** `python scripts/hw.py dedupe --course "<COURSE> Vault"`. It lists exact duplicate files. Then run it with `--delete` to remove the extras. Tell the user the count.

## Setup (once)

1. Install Python 3.12 from https://www.python.org/downloads/ (Windows: tick "Add python.exe to PATH").
2. Install the packages:

```bash
pip install rapidocr-onnxruntime pillow mss trafilatura lxml_html_clean yt-dlp fpdf2 pypdf faster-whisper sounddevice numpy python-pptx
```

Install only what the task needs: `fpdf2` PDFs, `pypdf` slides and merging, `rapidocr-onnxruntime pillow` OCR, `yt-dlp` video captions, `trafilatura lxml_html_clean` fetching, `faster-whisper` only for videos with no captions and no notes.

## Commands

All need `--course <name>`. Each prints the path it wrote. Output goes to the course vault automatically.

| Job | Command |
|---|---|
| Download a whole site (no summary) | `python scripts/hw.py grab URL --course C --depth 1 --videos` |
| Download a public page | `python scripts/hw.py fetch URL --course C` (`--depth 1` adds same-site links) |
| Save text you read in a browser | `python scripts/hw.py save --course C --label L --source URL` with text on stdin |
| Slides or notes to text | `python scripts/hw.py slides deck.pdf --course C` (pdf, pptx, txt) |
| Merge PDFs into one (skips duplicates) | `python scripts/hw.py merge FOLDER --glob "*.pdf" --course C` |
| Picture of a web page (page only) | `python scripts/hw.py webshot URL --course C --label L` (headless Edge or Chrome) |
| Screenshot of the screen | `python scripts/hw.py shot --course C --label L [--region X Y W H] [--delay 3]` |
| OCR the question only | `python scripts/hw.py ocr image.png --course C --region X Y W H` |
| Video link to transcript | `python scripts/hw.py captions URL --course C --captions-only` |
| Auto-correct a transcript | `python scripts/hw.py fixcaptions transcript.txt --course C` |
| Transcribe a recording | `python scripts/hw.py transcribe file.mp4 --course C` |
| Record live audio | `python scripts/hw.py record --course C` (Ctrl+C stops) |
| Markdown to PDF | `python scripts/hw.py pdf --course C --title T --section notes\|homework\|exam` with markdown on stdin |
| Save a markdown note | `python scripts/hw.py note --course C --title T --kind lecture` with markdown on stdin |
| Duplicate scan | `python scripts/hw.py dedupe --course C [--delete]` |

Prefer `webshot` over `shot` for web pages. `shot` captures the whole desktop and may include private windows.

**Download only.** If the user wants the material downloaded without summaries, run `grab` and stop. Do not read the files and do not summarise. Pages behind a login need your browser tool instead.

## Workflow: user gives a course URL, or has a course page open

1. **Page open in the user's browser** (login pages like Moodle, Canvas, Blackboard; JavaScript pages): use your browser tool. It must share the user's sign-ins, for example the Claude in Chrome extension with the user already signed in on a Chrome tab. Headless `grab` and `webshot` have no sign-ins. List the page's sections and links with a script (link text only; some tools block URLs with query strings). Then run `scripts/expand.js` in the page, twice, to open hidden sections: accordions, tabs, "Show more". It clicks only closed toggles. It never clicks submit, delete, post, pay, send, save, or sign-out buttons, and you must not click those either.
2. **Public page**: run `fetch` or `grab`. If it reports "no text", use your browser tool.
3. **Crawl the whole site** when the user wants everything: every week, lecture, tutorial, lab, assignment, resource and assessment page. Run `expand.js` on each. Keep a list of visited URLs so you never loop. Stay on the course site.
4. Find the **lecture notes or slides** for every lecture (step 1 of Notes above). Find the **homework** (labs, tutorials, quizzes, assignments) and the **assessment and exam information**.

## Workflow: downloading course files (slides, lecture notes)

1. **One file at a time.** Download each file in its own step: one request, then check that the file arrived (name and size) before the next. Never run a loop that downloads many files in one call: browsers time out, ask "allow multiple downloads", or silently drop files. If the browser asks to allow multiple downloads, ask the user to click Allow, then continue.
2. Name files clearly: `<COURSE> <NN> <title>`, for example `ELEC1111 03 Topic 2 - Lecture Notes.pdf`, so they sort in course order. Move them into `1 Notes/Source files/`.
3. Remove duplicates and make one file: `merge` joins PDFs in order into one PDF named after the course, with a bookmark per source file, and skips exact duplicates. Add `--delete-dupes` to delete duplicate files. Ask the user before `--delete-sources`, which deletes the single files after merging.

## Workflow: videos (only when there are no notes)

Run `captions URL --captions-only` for each. Expect "HTTP 429" from YouTube; the script retries with waits. Then run `fixcaptions` and correct the text (next section). Transcribe audio with `faster-whisper` only if the user allows the large download.

## Workflow: correcting transcripts

Auto-captions mishear technical words ("print f", "maloc", "strruct"). Never fix silently where you are unsure.
1. Run `fixcaptions`. It uses the course's own vocabulary to fix clear mishearings and joins split words. Unsure cases get `[ambiguous: maybe X]`. It keeps the original and writes a log. Read the log and undo wrong changes. `--terms file.txt` adds words.
2. Correct by context with the slides, code pages and assignment text. Check every number, formula and line of code against a source.
3. If you cannot correct with confidence, write `[ambiguous]` (or `[ambiguous: could be X or Y]`). Never guess a number, formula, name or code.
4. End the notes with an **Ambiguities** list of everything marked.

## Watch next (video suggestions)

Suggest videos by **title and channel only**. Never watch or transcribe them. Use web search for real titles from well-known educational channels (for example 3Blue1Brown, Khan Academy, CrashCourse, MIT OpenCourseWare, Professor Leonard, StatQuest). Add a URL only if the search returned it. Never invent a title or URL. If you cannot search, list topics to look up.

## Assignment plan (advice only)

For each assignment write a plan, never a solution. **Never do the assignment for the user.** No solution code, no answers, no finished drafts. If asked to solve it, say you only give a plan, and make the plan more detailed. Include: the task in your own words; due date, late penalty, weight and marks split; the rules, including any ban on AI help (remind the student to write their own work); a day-by-day schedule from today to the due date with stage order and submit points; which lectures to review first; habits that save marks (test each part, submit early, style rules); common mistakes; how to get unstuck. Save with `pdf --section homework`.

## Past assignments

When the course site links earlier assignments or earlier terms, analyse the specs too: what each asked, stages, mark split, which topics they test, patterns that repeat. Put it in the exam and test preparation PDF or the plan. Analyse specs only. Never collect or reuse other students' solutions.

## Cost warning (tell the user before a big run)

This skill burns many tokens, because you must read the material:
- one lecture transcript: about 12,000 words, roughly 16,000 tokens
- reading **every** lecture-notes file of one course: for example ten files totalling 393 pages, roughly 150,000 to 250,000 tokens
- one assignment page with hidden sections opened: roughly 20,000 tokens
- every extra step re-reads the whole conversation, so real usage is higher

Tell the user before reading everything. A free plan will probably not cover a full course. Work through one topic at a time and save as you go.

## Dictation (Wispr Flow or any voice-to-text app)

Dictation apps type into the focused window, so it reaches you as ordinary text. Treat dictated remarks as the user's own notes. Add them word for word under "My notes".

## Rules

- Take a desktop screenshot only when the user asks, and say what was captured.
- Write only inside the course vault folder.
- If something is unreadable or missing, say so. Do not invent it.
- Keep exact numbers, names, dates and formulas from the source.
- The user, not this tool, answers for how the material is used. Follow the university's rules.
