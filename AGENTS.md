# Contributor Guide

## Project Structure
- `sync_clipboard.py`: main macOS-side sync loop (ADB + clipboard handling).
- `start_sync.command`: Finder-friendly launcher for the Python script.
- `ClipboardSync.app/`: macOS app bundle for Spotlight launch.
- `android_app/`: Android app (Accessibility Service + broadcast receiver).
- `requirements.txt`, `README.md`: Python dependencies and top-level usage docs.
- Treat `android_app/build/` as generated output; do not hand-edit build artifacts.

## Build and Test Commands
- Install Python deps: `python3 -m pip install -r requirements.txt`
- Run sync from terminal: `python3 sync_clipboard.py`
- Run sync from Finder: `./start_sync.command`
- Android build/install (from `android_app/`):
  - `./gradlew assembleDebug` (compile APK)
  - `./gradlew installDebug` (install on connected device)
  - `./gradlew test` (runs JVM unit tests when present)
- Quick device check: `adb devices`

## Style and Coding Guidelines
- Python: follow PEP 8 basics (4-space indentation, `snake_case`, small focused functions).
- Keep subprocess and ADB interactions explicit; surface errors with actionable logs.
- Android (Java): keep classes cohesive and naming descriptive (`MainActivity`, `WriteReceiver`, etc.).
- Minimize new dependencies; when adding external libraries/APIs, check latest Context7 docs first.

## Testing Expectations
- This repo currently relies heavily on manual validation.
- For behavioral changes, verify:
  1. Mac -> Android text sync
  2. Android -> Mac text sync
  3. Mac -> Android image sync
  4. Android -> Mac image sync
- If Android code changes, at least run `./gradlew assembleDebug`; include additional test output when relevant.
- Note any untested paths clearly in PR notes.

## Commit and PR Guidelines
- Use focused, atomic commits with imperative subject lines.
- Keep unrelated refactors out of feature/bugfix commits.
- PRs should include: purpose, approach, commands/tests run, and manual verification results.
- Mention device/ADB assumptions and any setup steps reviewers must reproduce.
