---
name: homework-vault
description: Build a study vault for one course: all slides merged into one PDF, a condensed notes PDF with slide references, YouTube links and practice problems, an exam preparation PDF with a timeline, a Homework folder of screenshots sorted by week (OCR of the questions only), and an Assignments folder with a plan, never a solution, for each take-home assignment. Use when the user gives a course URL, has a course page open, or asks for lecture summaries, homework capture, assignment planning or exam preparation.
---

# Homework Vault

Work runs locally. `scripts/hw.py` gathers material. **You** read it and write the summaries yourself. Do not call any other summariser.

## The output: one folder, five parts

Every course gets one folder named after the course, inside Downloads: `~/Downloads/homework-vault/<COURSE> Vault/` (for example `ELEC1111 Vault`). `hw.py` makes it from `--course ELEC1111`. It ends up holding exactly five things:

```
<COURSE> Vault/
  <COURSE> Slides.pdf      every lecture slide and note, merged into one file, in course order
  <COURSE> Notes.pdf       the condensed study guide: summaries, slide references, YouTube links, practice problems
  <COURSE> Exam Prep.pdf   dates, what each exam covers, what to practice, a countdown timeline
  Homework/                a FOLDER of screenshots, in subfolders by week (Week 1/, Week 2/ ...), plus Questions.md
  Assignments/             a FOLDER of assignment plan PDFs. It stays empty if all assessments are tests
```

Working files (page text, transcripts, downloads, the individual lecture PDFs) are temporary. They go in `_work/` or Downloads and are **deleted at the end** (see Finish). Only the five parts stay.

### 1. Slides: one file with all the slides
Collect every lecture-slides or lecture-notes file and join them in order with `merge` (it skips exact duplicates). Do not summarise here. This is the full original, so the Notes can point into it.

### 2. Notes: the condensed study guide (the main product)
Read **every slide of every file**. Do not sample, skip or stop early. Extract text with `slides`, and look at an image only when a diagram carries meaning. Condense hundreds of slides into **one** PDF: `pdf --course C --title "<COURSE> Notes"`. Aim for about 30 pages, scaled to the course. Say how long it came out. For each topic include:
- a short overview and the key concepts in plain words
- definitions and formulas, exact as the slides state them
- common mistakes the lecturer warned about
- **slide references**, like "Slides p. 120 to 135", pointing into `<COURSE> Slides.pdf`
- **YouTube and other resources**: title, channel and a clickable link. Include the lecture-recording and revision-video links from the course page. Find extra videos with web search. Never invent a title or URL, and never watch the videos
- **Practice problems**: (a) the practice and worked problems that appear in the lecture slides, copied or rewritten, with their slide page numbers and the answers where the slides give them; (b) extra problems of the same type that you write, with answers at the end of the PDF. Mark which are from the slides and which are yours

Write every link as `[label](https://...)`. The `pdf` command turns it into a clickable link. Use slides and notes first. If a lecture has slides or notes, do **not** transcribe its recording. Transcribe only lectures that have nothing written.

### 3. Exam Prep: the timeline
`pdf --course C --title "<COURSE> Exam Prep" --section exam`. Read the course outline, assessments page, quiz and exam pages, past papers, and the notes. Include:
- **When:** every exam, test, quiz and assignment deadline: date, time, room, length, weight, open or closed book, format. Write `[not published]` when you cannot find it. Never invent a date
- **What each covers:** the topics, from the outline and the notes
- **What to practice:** question types per topic, which slide and past-paper problems to redo, formulas to memorise, skills to drill
- **Past papers and solutions:** list and link them
- **A countdown timeline** from today to each exam: what to study each day or week, with time for practice papers
- weak spots and short exam-day tips

### 4. Homework: a folder of pictures, sorted by week (when the user asks for it)
Take **one screenshot for every homework page or question**, possibly hundreds, each named clearly (`--label q12`). Sort them into subfolders with `--group`: by week when you can (`--group "Week 3"`), otherwise by topic, tutorial, lab or quiz. They land in `Homework/<group>/`. Keep the pictures as files. Do not merge them into a PDF.

**Standard homework recipe, in this order:** (1) `slidepics` on the merged slides, for the lecture Example and Practice problems; (2) `pdfpics` on every workshop, tutorial and problem-set PDF, one at a time; (3) screenshots with `--region` OCR only when something exists only on a web page. Check one picture of each kind yourself before you say it is done: no logo, banner, answer or page number, and no circuit cut in half.

**Where homework comes from.** Look for workshop sheets, tutorials, problem sets and quizzes in every topic section. For a homework PDF, download it (one file at a time, see below) and run `pdfpics FILE --course C --group "Week 3" --label "Workshop 2"`. It turns every page into a picture in `Homework/<group>/`, cropped to the question content only: banners, headers, footers, logos, page numbers and watermarks are removed. All pages are joined into one strip and cut only on blank rows, so a circuit that a page break split in two is whole again and no circuit is ever cut in half, and the picture is limited to 64 colours to save space (about 70% smaller). `--keep-chrome` keeps everything, `--colors 0` turns the colour limit off. For pictures already saved uncropped, run `cleanpics --course C [--skip Quizzes] [--only text] [--top 0.115 --bottom 0.075]` once: it cuts the header and footer strips, a leftover header fragment above the header rule, and the white margins in place and saves the PDF's own text under the same name in `Questions.md`, so no OCR is needed for text PDFs. Group by the teaching week the work belongs to (use the course schedule: topic numbers and week numbers can differ). Do not picture PDFs that are only solutions: use `--no-text` or skip them.

**Practice problems in lecture slides.** The Example and Practice problem slides are the main homework. Run `slidepics SLIDES.pdf --course C --groups "Topic 1=1-62;Topic 2=63-122;..."` on the merged slides PDF (take the ranges from the notes course map). For every slide titled "Example n" or "Practice problem n" it saves a picture of the question and the circuit only, in `Homework/Slides/<Topic>/`, named like `Example 1 (Slides p. 69).png`. It keeps the whole question (title, every line of text, and the figure) and removes only the answer box, the page number and the logo. The question text goes to `Questions.md`. Answers stay in the Notes PDF.

**Quizzes.** Take pictures of the quiz information (rules, dates, platform instructions) into `Homework/Quizzes/`. Do **not** start or open a live quiz attempt, and never answer a quiz for the user. Quizzes are often on an external platform behind its own login. If the course outline marks assessments "No Assistance" (no generative AI), say so to the user. This tool is for studying, not for answering assessed work.

**OCR only the question itself:** look at the screenshot, find the question's rectangle, then run `ocr FILE --course C --region X Y W H`. That appends the question text to `Homework/Questions.md`, under the picture's folder and file name. Never OCR a whole page, answers, solutions, menus or page chrome.

### 5. Assignments: a plan for each take-home assignment (a folder)
Find out whether the course has take-home assignments (projects, reports, coding tasks). If **all assessments are tests and exams, leave `Assignments/` empty** and say so.

**Labs count too.** If the course has marked labs, write a **Lab Guide** PDF for `Assignments/` with `pdf --section assignment`, even if there are no other take-home assignments. Read the course outline, the lab student guide and the lab manual (introductions and component lists are enough). Include: how labs are marked (checkpoints, marks, attendance, catch-up rules), what to buy and bring, safety rules, and for each lab its aims, parts, which lecture topics to revise, and how to prepare. Include the hurdle test and the final lab exam. Give no pre-lab answers and no measurements. Remind the student that lab work is individual.

If there are assignments, write a plan for **each** one with `pdf --course C --title "<Assignment name> Plan" --section assignment`. Scrape the whole assignment page first: open every hidden section with `expand.js`, and read every stage, step, rule and marking rule. The plan gives tips and advice on how to tackle it. **Never do the assignment for the user.** No solution code, no answers, no pseudo-code of the solution, no finished drafts. **Never open, edit or write the student's own code or work files.** If asked to solve it, say you only give a plan, and make the plan more detailed. Include:
- the task in your own words, and every stage or step from the page, in order, with what each one asks for
- due date, late penalty, weight, and how the marks split
- the rules, including any ban on AI help (remind the student to write their own work)
- a day-by-day schedule from today to the due date, with stage order and submit points
- which lectures and slide pages to review before each step
- tips for each step: what to think about, what to test, how to check progress, which provided tools or tests to use
- habits that save marks (test each part, submit early, style rules from the rubric)
- common mistakes for this kind of task
- how to get unstuck: help sessions, forum rules, drawing diagrams, asking staff

## Finish: clean up (always, last step)

1. Run `python scripts/hw.py finish --course "<COURSE> Vault" --also-delete FILE...`. It removes exact duplicates, deletes the `_work` folder, and deletes every file in `--also-delete`. List there each file this run downloaded outside the vault, such as browser downloads in Downloads. It then prints what the vault holds.
2. The vault keeps only the five parts: three PDFs, `Homework/` and `Assignments/`. Tell the user what was deleted and how many duplicates were found.
3. Delete only files this run created. Never delete the user's own files. In **download-only** mode, do not delete anything: just run `dedupe`.

## Setup (once)

1. Install Python 3.12 from https://www.python.org/downloads/ (Windows: tick "Add python.exe to PATH").
2. Install the packages:

```bash
pip install rapidocr-onnxruntime pillow mss trafilatura lxml_html_clean yt-dlp fpdf2 pypdf pypdfium2 faster-whisper sounddevice numpy python-pptx
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
| Merge all slides into `<COURSE> Slides.pdf` (skips duplicates) | `python scripts/hw.py merge FOLDER --glob "*.pdf" --course C` |
| Picture of a web page (page only) | `python scripts/hw.py webshot URL --course C --label L [--group "Week 3"]` (headless Edge or Chrome) |
| Screenshot of the screen | `python scripts/hw.py shot --course C --label L [--group "Week 3"] [--region X Y W H] [--delay 3]` |
| Homework PDF into pictures by week (and its text) | `python scripts/hw.py pdfpics FILE --course C --group "Week 3" --label "Workshop 2"` |
| Slide Example and Practice problems as pictures (question and circuit only) | `python scripts/hw.py slidepics SLIDES.pdf --course C --groups "Topic 1=1-62;Topic 2=63-122"` |
| Re-crop pictures already saved (logos, headers, margins) | `python scripts/hw.py cleanpics --course C [--skip Quizzes]` |
| OCR the question only | `python scripts/hw.py ocr image.png --course C --region X Y W H` |
| Video link to transcript | `python scripts/hw.py captions URL --course C --captions-only` |
| Auto-correct a transcript | `python scripts/hw.py fixcaptions transcript.txt --course C` |
| Transcribe a recording | `python scripts/hw.py transcribe file.mp4 --course C` |
| Record live audio | `python scripts/hw.py record --course C` (Ctrl+C stops) |
| Markdown to PDF | `python scripts/hw.py pdf --course C --title T --section notes\|exam\|assignment` with markdown on stdin |
| Save a markdown note | `python scripts/hw.py note --course C --title T --kind lecture` with markdown on stdin |
| Duplicate scan | `python scripts/hw.py dedupe --course C [--delete]` |
| Finish: dedupe, delete working files | `python scripts/hw.py finish --course C --also-delete FILE...` |

Prefer `webshot` over `shot` for web pages. `shot` captures the whole desktop and may include private windows.

**Download only.** If the user wants the material downloaded without summaries, run `grab` and stop. Do not read the files and do not summarise. Pages behind a login need your browser tool instead.

## Workflow: user gives a course URL, or has a course page open

1. **Page open in the user's browser** (login pages like Moodle, Canvas, Blackboard; JavaScript pages): use your browser tool. It must share the user's sign-ins, for example the Claude in Chrome extension with the user already signed in on a Chrome tab. Headless `grab` and `webshot` have no sign-ins. List the page's sections and links with a script (link text only; some tools block URLs with query strings). Then run `scripts/expand.js` in the page, twice, to open hidden sections: accordions, tabs, "Show more". It clicks only closed toggles. It never clicks submit, delete, post, pay, send, save, or sign-out buttons, and you must not click those either.
2. **Public page**: run `fetch` or `grab`. If it reports "no text", use your browser tool.
3. **Crawl the whole site** when the user wants everything: every week, lecture, tutorial, lab, assignment, resource and assessment page. Run `expand.js` on each. Keep a list of visited URLs so you never loop. Stay on the course site.
4. Find the **lecture notes or slides** for every lecture (step 1 of Notes above). Find the **homework** (labs, tutorials, quizzes, assignments) and the **assessment and exam information**.

## Workflow: downloading course files (slides, lecture notes)

1. **One file at a time.** Use `scripts/download.js` in the logged-in page (it saves to the browser's Downloads folder and finds the real file behind Moodle "resource" links). If the browser tab stops responding (a frozen tab or a hidden prompt), open a new tab on the course page and carry on there, and tell the user to check Chrome for a prompt. Name every download starting with `hwtmp`, so `finish --also-delete hwtmp*` can remove them. Download each file in its own step: one request, then check that the file arrived (name and size) before the next. Never run a loop that downloads many files in one call: browsers time out, ask "allow multiple downloads", or silently drop files. If the browser asks to allow multiple downloads, ask the user to click Allow, then continue.
2. Name files clearly: `<COURSE> <NN> <title>`, for example `ELEC1111 03 Topic 2 - Lecture Notes.pdf`, so they sort in course order. Leave them where they land. `merge` reads them, and `finish` deletes them.
3. Remove duplicates and make one file: `merge` joins PDFs in order into one PDF named after the course, with a bookmark per source file, and skips exact duplicates. Add `--delete-dupes` to delete duplicate files. Ask the user before `--delete-sources`, which deletes the single files after merging.

## Optional: local receiver (a browser page sends files straight into the vault)

`python scripts/hw.py receive --course C` starts a small server on 127.0.0.1 and prints a token. `scripts/send.js` lets a logged-in page post files and pictures to it. Chrome may block this until the user allows access to the local network, and in testing the prompt blocked the page. If the page's request hangs, stop and use `scripts/download.js` instead.

## When a course has no slides or notes

Never make up slides. If there are no lecture slides or notes:
- Do not create `<COURSE> Slides.pdf` (leave it out and say so), and do not write "Slides p." references.
- Build the Notes from the lecture transcripts. Use the default free captions (`captions URL --captions-only`) unless the user asks for Whisper. Cite where each point comes from by lecture name, and give a timestamp if the transcript has one.
- Treat auto-captions as about nine words in ten right: technical words, names, numbers and formulas are the weak part. Run `fixcaptions`, mark every doubtful number, formula or term `[ambiguous]`, and never fill a gap with a guess.
- Say clearly in the Notes that they come from captions, not from the lecturer's slides.
- Practice problems: use only problems the lecturer actually states in the transcript, and label problems you write yourself as extra.

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

## Past assignments

When the course site links earlier assignments or earlier terms, analyse the specs too: what each asked, stages, mark split, which topics they test, patterns that repeat. Put it in the assignment plan, and in the exam and test preparation PDF where it applies. Analyse specs only. Never collect or reuse other students' solutions.

## Cost warning (tell the user before a big run)

This skill burns many tokens, because you must read the material:
- one lecture transcript: about 12,000 words, roughly 16,000 tokens
- reading **every** lecture-notes file of one course as text: for example ten files totalling 393 slides were about 28,500 words, roughly 40,000 tokens. The course outline, a lab manual of about 20,000 words, and past exams add more
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
