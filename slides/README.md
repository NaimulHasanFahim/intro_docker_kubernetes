# The deck

Upload `docker-k8s-intro.pptx` to Google Drive → **Open with ▸ Google Slides**, or open
it directly in PowerPoint, Keynote or LibreOffice. Speaker notes are included.

| File | What it is |
|---|---|
| `docker-k8s-intro.pptx` | 62 slides — the full deck |
| `docker-k8s-intro-lean.pptx` | 46 slides — the cut for a tight 90 minutes |
| `content.py` | All slide content — the single source of truth |
| `build_pptx.py` | Renders `content.py` into both decks and `deck.md` |
| `deck.md` / `deck-lean.md` | Marp markdown, generated — do not hand-edit |

## Rebuilding

```bash
python3 build_pptx.py          # 62 slides -> docker-k8s-intro.pptx + deck.md
python3 build_pptx.py --lean   # 46 slides -> *-lean.pptx + deck-lean.md
```

Pure standard library — no `pip install`, no Node.

## Editing

Edit `content.py`, never the `.pptx` or the `.md`. Each slide is a dict:

```python
{"title": "...", "lead": "...", "bullets": [...], "code": "...",
 "diagram": {...}, "table": [[...], ...], "footnote": "...",
 "notes": "...", "core": True}
```

`{"type": "section"}` makes a divider. `{"type": "gag", "emoji": "🐳", "punchline": "..."}`
makes a joke slide — the gags sit right after the heaviest concepts on purpose, each
restating the idea in plain language for anyone who drifted. `"lean": False` drops a
slide from the lean build.

The palette (cream `#F6F3E7`, forest `#1D3A1C`, sage `#7F9169`) is six constants at the
top of `build_pptx.py`. The demo app's UI uses the same values, so changing them reskins
both together.

> The `.pptx` files were validated structurally but never opened in a renderer —
> LibreOffice on the build machine cannot load any file. Open one yourself before the
> session.
