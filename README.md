# homework-vault

A skill file (`SKILL.md`) plus one local script. It lets an LLM agent summarise lectures and save homework screenshots into a notes vault (Obsidian-style folders of markdown).

- Runs on your machine. Transcription uses `faster-whisper`; screenshots use `mss`.
- The LLM that loads the skill writes the summaries. No API key is part of this repo.
- Inputs: a course URL (public, or a page open in your browser when the agent has a browser tool), video links, recordings, live mic audio, slides (pdf/pptx), screenshots.
- Output (in your Downloads folder): a notes PDF with lecture summaries and concepts, a picture of the homework page, and an assignment plan PDF. The plan is advice only; it never does the assignment for you.

## Token cost (read this first)

The LLM has to read everything it summarises, so a full course uses a lot of tokens:

| Material | Rough size |
|---|---|
| One lecture transcript (about 12,000 words) | 16,000 tokens |
| A course with 18 lectures | 300,000 tokens to read, plus the notes it writes |
| One assignment page, hidden sections opened | 20,000 tokens |

Each step also re-reads the whole conversation, so real usage is higher. **A free plan will probably not work for a whole course.** Use a paid plan or API credit, or run one week at a time. The script itself (captions, OCR, PDF, screenshots) is free and runs on your PC. Only the LLM's reading and writing cost tokens.

## Accuracy

Auto-captions mishear technical words. `fixcaptions` repairs clear mistakes with the course's own vocabulary and logs every change. Anything it or the LLM cannot fix with confidence is marked `[ambiguous]` in the notes and listed at the end, so nothing is guessed silently. Always check marked passages against the source.

## Academic integrity

This tool helps you organise and understand your own study material. For assignments it files the task and writes a plan; it does not do the assignment for you. Follow your university's rules on AI use and recording lectures. You are responsible for how you use it.

## Install

1. **Install Python 3.12** from https://www.python.org/downloads/ . On Windows, tick "Add python.exe to PATH" in the installer. Check with `python --version`.
2. Copy this folder into your agent's skills folder (for Claude Code: `~/.claude/skills/homework-vault/`).
3. Install the packages: `pip install rapidocr-onnxruntime mss trafilatura lxml_html_clean yt-dlp fpdf2 faster-whisper sounddevice numpy pypdf python-pptx`
4. Optional: set `HW_VAULT` to use another output folder. By default everything goes to `Downloads/homework-vault/<course>/`.

## Layout in the vault

```
<output>/<course>/*.pdf           lecture notes and assignment plans
<output>/<course>/attachments/   screenshots and page pictures
<output>/<course>/sources/       transcripts, slide text
<output>/<course>/notes/         summaries and homework notes
```

## Licence

MIT. Do what you like with it.
