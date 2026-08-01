# The deck

Upload `docker-k8s-intro.pptx` to Google Drive → **Open with ▸ Google Slides**, or open
it directly in PowerPoint, Keynote or LibreOffice. Speaker notes are included.

| File | What it is |
|---|---|
| `docker-k8s-intro.pptx` | 62 slides — the full deck |
| `docker-k8s-intro-lean.pptx` | 46 slides — the cut for a tight 90 minutes |
| `docker-k8s-intro-final.pptx` | an earlier export, kept as a spare |
| `deck.md` | the full deck in [Marp](https://marp.app) markdown |

## The markdown deck

Preview it with the *Marp for VS Code* extension, or export:

```bash
npx @marp-team/marp-cli deck.md -o deck.html
npx @marp-team/marp-cli deck.md --pdf
```

It renders in Marp's default theme. `<!-- _class: lead -->` still gives the divider and
joke slides their inverted look; the `emoji` and `kicker` spans are plain text unless you
add CSS for them in the front matter.

## Editing

Edit these files directly — the generator that produced them is no longer in the repo,
so the `.pptx` files and the markdown decks are now separate copies. A change to one does
not reach the other.
