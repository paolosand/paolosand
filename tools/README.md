# tools

Generators for the riso-print SVGs in `../assets`. Both emit **pure `<path>` outlines**
rather than `<text>`, so the cards render identically for every visitor — GitHub strips
webfonts from README SVGs, and live `font-family` would silently fall back to whatever
mono the viewer happens to have.

Type is JetBrains Mono (the portfolio's primary typeface), subset to the glyphs actually
used — `fonts/*.ttf` are ~8 KB each.

## signals — live, automated

`gen_signals.py` pulls **public** GitHub activity via the GraphQL API and renders the
52-week contribution grid, headline counts, and language mix.

Runs daily via [`update-signals.yml`](../.github/workflows/update-signals.yml), which skips
the commit when the rendered SVG is byte-identical. In practice it commits most days, since
the 52-week window slides and the date stamp advances. Because it reads public data only,
the default `GITHUB_TOKEN` is sufficient — no personal access token, no secret to rotate.

> Private contributions are therefore **not** counted. To include them you'd need a classic
> PAT with `read:user` exposed as a secret, and to swap `contributionsCollection` to query
> `viewer` instead of `user(login:)`.

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
