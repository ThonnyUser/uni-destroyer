# homework-vault

A skill file (`SKILL.md`) plus one local script. It lets an LLM agent summarise lectures and save homework screenshots into a notes vault (Obsidian-style folders of markdown).

- Runs on your machine. Transcription uses `faster-whisper`; screenshots use `mss`.
- The LLM that loads the skill writes the summaries. No API key is part of this repo.
- Inputs: a course URL (public, or a page open in your browser when the agent has a browser tool), video links, recordings, live mic audio, slides (pdf/pptx), screenshots.
- Output (in your Downloads folder): a notes PDF with lecture summaries and concepts, a picture of the homework page, and an assignment plan PDF. The plan is advice only; it never does the assignment for you.

## Download only (free, no summaries)

You can use the tool just to download a course, with no LLM and no tokens. Run it yourself in a terminal:

```bash
python scripts/hw.py grab https://your-course-site/ --course maths --depth 1 --videos
```

It saves into `Downloads/homework-vault/maths Vault/_work/` (kept as it is in this mode, nothing is cleaned up):

- every page it reaches as plain text (`_work/`), with JavaScript pages loaded in a headless Edge or Chrome
- linked files from the same site: pdf, pptx, docx, code files (`_work/files/`)
- captions for every YouTube link it finds (`--videos`), saved as text
- `index.md`, a list of everything found and what was saved

Options: `--depth 0` is one page only. `--max-pages 30` caps the crawl. `--max-mb 50` skips big files. `--pace 25` waits between videos, because YouTube answers "HTTP 429" if asked too fast. Videos with no captions are listed in `index.md` and skipped.

Limits: pages behind a login show only the login screen. For those, open the page in your browser and let an agent with a browser tool read it. `fixcaptions` (free, also local) can clean up the caption text afterwards. To get summaries and notes, load `SKILL.md` into an LLM agent. That part costs tokens.

## Token cost (read this first)

The LLM has to read everything it summarises, so a full course uses a lot of tokens:

| Material | Rough size |
|---|---|
| One lecture transcript (about 12,000 words) | 16,000 tokens |
| A course with 18 lectures | 300,000 tokens to read, plus the notes it writes |
| Reading every lecture-notes file of one course (for example ten PDFs, 393 pages) | 150,000 to 250,000 tokens |
| One assignment page, hidden sections opened | 20,000 tokens |

Each step also re-reads the whole conversation, so real usage is higher. **A free plan will probably not work for a whole course.** Use a paid plan or API credit, or run one week at a time. The script itself (captions, OCR, PDF, screenshots) is free and runs on your PC. Only the LLM's reading and writing cost tokens.

## Accuracy

Auto-captions mishear technical words. `fixcaptions` repairs clear mistakes with the course's own vocabulary and logs every change. Anything it or the LLM cannot fix with confidence is marked `[ambiguous]` in the notes and listed at the end, so nothing is guessed silently. Always check marked passages against the source.

## Academic integrity

This tool helps you organise and understand your own study material. For assignments it files the task and writes a plan; it does not do the assignment for you. Follow your university's rules on AI use and recording lectures. You are responsible for how you use it.

## Install

1. **Install Python 3.12** from https://www.python.org/downloads/ . On Windows, tick "Add python.exe to PATH" in the installer. Check with `python --version`.
2. Copy this folder into your agent's skills folder (for Claude Code: `~/.claude/skills/homework-vault/`).
3. Install the packages: `pip install rapidocr-onnxruntime pillow mss trafilatura lxml_html_clean yt-dlp fpdf2 pypdf faster-whisper sounddevice numpy python-pptx`
4. Optional: set `HW_VAULT` to use another output folder. By default everything goes to `Downloads/homework-vault/<course>/`.
5. **Only for pages behind a login** (Moodle, Canvas, Blackboard): your agent needs a browser tool that uses your own sign-ins, such as the [Claude in Chrome extension](https://chromewebstore.google.com/detail/fcoeoabgfenejglbffodgkkbkcdhcgfn). Sign in to the site in Chrome first. Public pages, downloads and the `grab` command need no extra tool.

## What you get

One folder per course, named after the course, in your Downloads folder. It ends up with three PDFs:

```
Downloads/homework-vault/ELEC1111 Vault/
  ELEC1111 Slides.pdf      every lecture slide merged into one file
  ELEC1111 Notes.pdf       the condensed study guide (about 30 pages): summaries, slide references, YouTube links, practice problems
  ELEC1111 Exam Prep.pdf   exam and test dates, what each covers, what to practice, a countdown timeline
  Homework/                optional: screenshots of homework, OCR of the questions only, assignment plan
```

At the end the tool deletes every temporary file it used (downloads, page text, transcripts) and removes duplicates. Slides are used instead of transcribing recordings, which saves a lot of tokens.

## Download only (free, no summaries)

You can use the tool just to download a course, with no LLM and no tokens. Run it yourself in a terminal:

```bash
python scripts/hw.py grab https://your-course-site/ --course maths --depth 1 --videos
```

It saves into `Downloads/homework-vault/maths Vault/_work/` (kept as it is in this mode, nothing is cleaned up):

- every page it reaches as plain text (`_work/`), with JavaScript pages loaded in a headless Edge or Chrome
- linked files from the same site: pdf, pptx, docx, code files (`_work/files/`)
- captions for every YouTube link it finds (`--videos`), saved as text
- `index.md`, a list of everything found and what was saved

Options: `--depth 0` is one page only. `--max-pages 30` caps the crawl. `--max-mb 50` skips big files. `--pace 25` waits between videos, because YouTube answers "HTTP 429" if asked too fast. Videos with no captions are listed in `index.md` and skipped.

Limits: pages behind a login show only the login screen. For those, open the page in your browser and let an agent with a browser tool read it. `fixcaptions` (free, also local) can clean up the caption text afterwards. To get summaries and notes, load `SKILL.md` into an LLM agent. That part costs tokens.

## Token cost (read this first)

The LLM has to read everything it summarises, so a full course uses a lot of tokens:

| Material | Rough size |
|---|---|
| One lecture transcript (about 12,000 words) | 16,000 tokens |
| A course with 18 lectures | 300,000 tokens to read, plus the notes it writes |
| Reading every lecture-notes file of one course (for example ten PDFs, 393 pages) | 150,000 to 250,000 tokens |
| One assignment page, hidden sections opened | 20,000 tokens |

Each step also re-reads the whole conversation, so real usage is higher. **A free plan will probably not work for a whole course.** Use a paid plan or API credit, or run one week at a time. The script itself (captions, OCR, PDF, screenshots) is free and runs on your PC. Only the LLM's reading and writing cost tokens.

## Accuracy

Auto-captions mishear technical words. `fixcaptions` repairs clear mistakes with the course's own vocabulary and logs every change. Anything it or the LLM cannot fix with confidence is marked `[ambiguous]` in the notes and listed at the end, so nothing is guessed silently. Always check marked passages against the source.

## Academic integrity

This tool helps you organise and understand your own study material. For assignments it files the task and writes a plan; it does not do the assignment for you. Follow your university's rules on AI use and recording lectures. You are responsible for how you use it.

## Install

1. **Install Python 3.12** from https://www.python.org/downloads/ . On Windows, tick "Add python.exe to PATH" in the installer. Check with `python --version`.
2. Copy this folder into your agent's skills folder (for Claude Code: `~/.claude/skills/homework-vault/`).
3. Install the packages: `pip install rapidocr-onnxruntime pillow mss trafilatura lxml_html_clean yt-dlp fpdf2 pypdf faster-whisper sounddevice numpy python-pptx`
4. Optional: set `HW_VAULT` to use another output folder. By default everything goes to `Downloads/homework-vault/<course>/`.
5. **Only for pages behind a login** (Moodle, Canvas, Blackboard): your agent needs a browser tool that uses your own sign-ins, such as the [Claude in Chrome extension](https://chromewebstore.google.com/detail/fcoeoabgfenejglbffodgkkbkcdhcgfn). Sign in to the site in Chrome first. Public pages, downloads and the `grab` command need no extra tool.

## What you get

Every course gets one folder, named after the course, in your Downloads folder. It always has three parts:

```
Downloads/homework-vault/ELEC1111 Vault/
  1 Notes/         ELEC1111 Notes.pdf       one big summary of every lecture-notes file, with links (about 30 pages)
    Source files/  downloaded notes, page text, transcripts
  2 Homework/      a screenshot of every homework, Questions.md (OCR of the questions only), assignment plan
  3 Exam Prep/     ELEC1111 Exam Prep.pdf   exam and test dates, what each covers, what to practice, a countdown plan
```

At the end of every run the tool scans for duplicate files (`dedupe`). Lecture slides and notes are used instead of transcribing recordings, which saves a lot of tokens.

## Licence

MIT. Do what you like with it.
