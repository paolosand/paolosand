# tools

Generators for the riso-print SVGs in `../assets`. Both emit **pure `<path>` outlines**
rather than `<text>`, so the cards render identically for every visitor — GitHub strips
webfonts from README SVGs, and live `font-family` would silently fall back to whatever
mono the viewer happens to have.

Type is JetBrains Mono (the portfolio's primary typeface), subset to the glyphs actually
used — `fonts/*.ttf` are ~8 KB each.

## signals — live, automated

`gen_signals.py` pulls GitHub activity via the GraphQL API and renders the 52-week
contribution grid, headline counts, and language mix.

Runs daily via [`update-signals.yml`](../.github/workflows/update-signals.yml), which skips
the commit when the rendered SVG is byte-identical. In practice it commits most days, since
the 52-week window slides and the date stamp advances. The default `GITHUB_TOKEN` is
sufficient — no personal access token, no secret to rotate.

> **On private work.** The token is unprivileged, so it sees exactly what any visitor sees.
> That still includes private *contribution counts*, because this account has
> **Settings → Profile → "Include private contributions on my profile"** enabled — the same
> reason the graph on the profile page shows them. Turn that setting off and this card drops
> to public-only automatically. Repo count and language mix are always public-only, since
> they query `privacy: PUBLIC` directly.

```bash
cd tools
pip install fonttools
GITHUB_TOKEN=$(gh auth token) python gen_signals.py ../assets
```

Note: running locally with *your own* token returns your full contribution count including
private work, so the numbers will read higher than what CI produces. CI output is the
public-only figure — that's the intended one.

## banner — static

`gen_banner.py` renders the wordmark. It only needs regenerating if the name, role lines,
or credentials change.

```bash
cd tools
python gen_banner.py ../assets
```

Both scripts write a light and a `-dark` variant; the README selects between them with
`<picture media="(prefers-color-scheme: dark)">`.
