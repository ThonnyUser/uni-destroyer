# homework-vault

A skill file (`SKILL.md`) plus one local script. It lets an LLM agent summarise lectures and save homework screenshots into a notes vault (Obsidian-style folders of markdown).

- Runs on your machine. Transcription uses `faster-whisper`; screenshots use `mss`.
- The LLM that loads the skill writes the summaries. No API key is part of this repo.
- Inputs: recordings, live mic audio, slides (pdf/pptx), screenshots.

## Academic integrity

This tool helps you organise and understand your own study material. It does not solve homework: the skill tells the LLM to capture and file assignments, not to answer them. Follow your university's rules on AI use and recording lectures. You are responsible for how you use it.

## Install

1. **Install Python 3.12** from https://www.python.org/downloads/ . On Windows, tick "Add python.exe to PATH" in the installer. Check with `python --version`.
2. Copy this folder into your agent's skills folder (for Claude Code: `~/.claude/skills/homework-vault/`).
3. Install the packages: `pip install rapidocr-onnxruntime mss faster-whisper sounddevice numpy pypdf python-pptx`
4. Set `HW_VAULT` to your vault folder.

## Layout in the vault

```
<vault>/<course>/attachments/   screenshots
<vault>/<course>/sources/       transcripts, slide text
<vault>/<course>/notes/         summaries and homework notes
```

## Licence

MIT. Do what you like with it.
