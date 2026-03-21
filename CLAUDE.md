# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LogMon is a Python 3 log file monitoring tool by VGX Consulting. It scans log directories for `*.log` files, matches error patterns via compiled regex, and sends HTML email alerts via SMTP/SSL. Designed for headless Linux servers, deployed as a standalone PyInstaller executable run via cron.

**Current version:** `1.4.5` (defined in `__version__` in `log_monitor.py`)

## Architecture

Single-file application (`log_monitor.py`, ~350 lines) with one class `LogMonitor`:

- **No runtime dependencies** — uses only Python standard library
- **Configuration:** INI file (`log_monitor.conf`) with environment variable overrides (`VGX_LM_*`)
- **Concurrency:** `ThreadPoolExecutor` with `os.cpu_count()` workers for parallel file scanning
- **Incremental scanning:** Tracks last-check timestamp in `.last_check` file; skips unmodified files
- **State files:** Written to script directory, falls back to `/tmp/vgx.logmonitor` if not writable

## Commands

```bash
# Run locally
python3 log_monitor.py --debug     # Debug mode with verbose output
python3 log_monitor.py --version   # Print version
python3 log_monitor.py             # Normal mode (silent unless errors)

# Build standalone executable
pip install pyinstaller
pyinstaller --onefile --name log_monitor log_monitor.py
# Output: dist/log_monitor

# No test suite exists — manual testing via --debug flag
```

## Release Process

Releases are automated via GitHub Actions (`.github/workflows/release.yml`):

```bash
git tag v1.3.3
git push origin main && git push origin v1.3.3
```

This builds a Linux x86_64 standalone executable and creates a GitHub Release with `log_monitor-v{VERSION}-linux-x86_64.tar.gz`.

## Version Bumping

When changing the version, update **both**:
1. `__version__` in `log_monitor.py` (line 27)
2. Version references in `README.md`

## Key Conventions

- **Copyright header** required on all code files: `© 2026 VGX Consulting. All rights reserved.`
- **Configuration secrets** (`log_monitor.conf`) are gitignored — only `log_monitor.conf.example` is tracked
- Error patterns are defined as a class-level list in `LogMonitor.error_patterns` and compiled into a single regex at init
- The `_create_html_email()` method generates inline-styled HTML (no external templates)
