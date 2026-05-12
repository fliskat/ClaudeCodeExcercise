# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git workflow

After every meaningful change, commit and push to GitHub immediately so work is never lost and the history is easy to revert.

- Commit after each logical unit of work (a feature added, a bug fixed, a color changed — not batched together)
- Write clean, descriptive commit messages: what changed and why, not just "update file"
- Always push after committing: `git add <files> && git commit -m "..." && git push`

## Running the project

Open `tictactoe.html` directly in a browser — no build step, no server required.

## Architecture

Single self-contained HTML file with three sections:

- **CSS** (`:root` vars → layout → component styles) — all theming is driven by two CSS custom properties: `--cx` (Player X color) and `--co` (Player O color). Change these to retheme both players globally.
- **HTML** — static shell: scoreboard (`#sx`, `#so`), status line (`#st`), board container (`#board`), reset button (`#rBtn`), flash overlay (`#flash`).
- **JS** (inline `<script>`) — no framework. Key functions:
  - `newGame()` — resets `cells[]`, `turn`, `over`; calls `render()` + `hud()`
  - `move(i)` — writes to `cells[i]`, calls `checkWin()`, advances turn or ends game
  - `render(winCombo?)` — rebuilds `#board` innerHTML from scratch each turn; draws win line via inline SVG if `winCombo` is passed
  - `hud()` — syncs status text and active-player highlight on scoreboard
  - `checkWin()` — tests all 8 combos in `WINS` constant; returns winning triple or `null`

Score is kept in a plain `{X:0, O:0}` object and persists across games within the same page session only.

## Hardcoded color values to be aware of

Several `drop-shadow` filters and `rgba` glow values in the CSS still reference the original cyan (`#00f5ff` / `rgba(0,245,255,…)`) for Player X visual effects (lines 34–37, 94, 177, 185–186). If `--cx` is changed again, update these hardcoded values to match.
