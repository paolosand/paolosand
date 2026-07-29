"""Generate the live SIGNALS card from public GitHub data.

Runs in CI on a schedule. Uses only PUBLIC activity, so the default
GITHUB_TOKEN is sufficient — no personal access token required.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from text2path import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_BOLD = os.path.join(HERE, "fonts", "JetBrainsMono-ExtraBold.ttf")
FONT_MED = os.path.join(HERE, "fonts", "JetBrainsMono-Medium.ttf")

LOGIN = os.environ.get("GH_LOGIN", "paolosand")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

W, H = 960, 392
PAD = 40

INK, PAPER = "#1A130A", "#F2EBDA"
PINK, BLUE, MINT, LEMON = "#F0457B", "#2841E8", "#00A076", "#E8B91A"

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ firstDay contributionDays{ date contributionCount } }
      }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
      totalCount
      nodes{ languages(first:12, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } }
    }
  }
}
"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "riso-signals",
        },
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def summarize(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]

    langs = {}
    for node in user["repositories"]["nodes"]:
        for e in node["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total_bytes = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]

    return {
        "total": cal["totalContributions"],
        "weeks": weeks,
        "active_days": sum(1 for d in days if d["contributionCount"] > 0),
        "best_day": max((d["contributionCount"] for d in days), default=0),
        "repos": user["repositories"]["totalCount"],
        "langs": [(n, s * 100.0 / total_bytes) for n, s in top],
        "other": 100.0 - sum(s * 100.0 / total_bytes for _, s in top),
    }


def heat_scale(dark):
    if dark:
        return ["#241E14", "#22306E", "#2A44B0", "#3E5AE0", "#7A8BF5"]
    return ["#E2D8BC", "#C3CBF2", "#8E9BEC", "#5265E9", "#2841E8"]


def build(s, dark=False):
    bg = INK if dark else PAPER
    fg = PAPER if dark else INK
    muted = "#8C7F63" if dark else "#7A6C53"
    faint = "#6E624A" if dark else "#9A8C70"
    track = "#332B1E" if dark else "#DDD2B5"
    blue = "#5C72F2" if dark else BLUE

    bold = lambda px, tr=0.0: Typesetter(FONT_BOLD, px, tr)
    med = lambda px, tr=0.0: Typesetter(FONT_MED, px, tr)

    out = []

    def draw(ts, text, x, y, color, anchor="start"):
        if anchor == "end":
            x -= ts.measure(text)
        elif anchor == "middle":
            x -= ts.measure(text) / 2
        paths, _ = ts.run_paths([(text, color)], x, y)
        for d, c in paths:
            out.append(f'  <path d="{d}" fill="{c}"/>')

    # ---------- header bar ----------
    out.append(f'  <rect x="0" y="0" width="{W}" height="36" fill="{fg}"/>')
    # the bar is filled with `fg`, so bar text must contrast against `fg`, not `bg`
    bar_accent = BLUE if dark else LEMON
    bar_meta = "#6E624A" if dark else "#B6A988"
    draw(bold(12, 0.26), "SIGNALS", PAD, 23, bg)
    draw(med(11, 0.14), f"@{LOGIN}", 190, 23, bar_accent)
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y").upper()
    draw(med(10, 0.18), f"AUTO-UPDATED {stamp}", W - PAD, 23, bar_meta, "end")

    # ---------- contribution heatmap ----------
    weeks = s["weeks"]
    gap = 3
    grid_x, grid_y = PAD, 86
    # size cells so the grid spans the full content width, flush with the language bar
    pitch = (W - PAD * 2 + gap) / len(weeks)
    cell = pitch - gap
    scale = heat_scale(dark)
    peak = max(1, s["best_day"])

    draw(med(10, 0.2), "PUBLIC CONTRIBUTIONS · LAST 52 WEEKS", PAD, 68, muted)

    # month ticks
    seen = set()
    for i, wk in enumerate(weeks):
        dt = datetime.strptime(wk["firstDay"], "%Y-%m-%d")
        key = (dt.year, dt.month)
        if dt.day <= 7 and key not in seen:
            seen.add(key)
            draw(med(8.5, 0.16), dt.strftime("%b").upper(), grid_x + i * pitch, grid_y - 6, faint)

    for i, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            wd = datetime.strptime(d["date"], "%Y-%m-%d").weekday()
            wd = (wd + 1) % 7  # Sunday-first rows
            n = d["contributionCount"]
            if n == 0:
                lv = 0
            else:
                ratio = n / peak
                lv = 1 + min(3, int(ratio * 4))
            out.append(
                f'  <rect x="{grid_x + i * pitch:.2f}" y="{grid_y + wd * pitch:.2f}" '
                f'width="{cell:.2f}" height="{cell:.2f}" fill="{scale[lv]}"/>'
            )

    grid_w = len(weeks) * pitch - gap
    grid_bottom = grid_y + 7 * pitch - gap

    # legend
    leg = med(8.5, 0.16)
    more_w = leg.measure("MORE")
    lx = W - PAD - more_w - 6 - 5 * pitch
    draw(leg, "LESS", lx - 8, grid_bottom + 21, faint, "end")
    for i, c in enumerate(scale):
        out.append(
            f'  <rect x="{lx + i * pitch:.2f}" y="{grid_bottom + 12}" '
            f'width="{cell:.2f}" height="{cell:.2f}" fill="{c}"/>'
        )
    draw(leg, "MORE", W - PAD, grid_bottom + 21, faint, "end")

    # ---------- stat row ----------
    sy = grid_bottom + 66
    stats = [
        (f"{s['total']:,}", "CONTRIBUTIONS", blue),
        (str(s["repos"]), "PUBLIC REPOS", PINK),
        (str(s["active_days"]), "ACTIVE DAYS", MINT),
        (str(s["best_day"]), "BUSIEST DAY", LEMON),
    ]
    col_w = (W - PAD * 2) / 4
    for i, (num, label, color) in enumerate(stats):
        x = PAD + i * col_w
        draw(bold(30), num, x, sy, fg)
        out.append(f'  <rect x="{x + 1}" y="{sy + 9}" width="22" height="5" fill="{color}"/>')
        draw(med(9.5, 0.2), label, x, sy + 30, muted)

    # ---------- language strip ----------
    ly = sy + 62
    draw(med(10, 0.2), "MOST USED · PUBLIC REPOS", PAD, ly, muted)

    bar_y = ly + 12
    bar_w = W - PAD * 2
    inks = [BLUE, PINK, MINT, LEMON, "#9A8C70" if dark else "#7A6C53"]
    out.append(f'  <rect x="{PAD}" y="{bar_y}" width="{bar_w}" height="16" fill="{track}"/>')
    cx = PAD
    for i, (name, pct) in enumerate(s["langs"]):
        seg = bar_w * pct / 100.0
        out.append(f'  <rect x="{cx:.1f}" y="{bar_y}" width="{seg:.1f}" height="16" fill="{inks[i]}"/>')
        cx += seg

    # legend under the bar
    gy = bar_y + 34
    gx = PAD
    lg = med(9.5, 0.14)
    for i, (name, pct) in enumerate(s["langs"]):
        out.append(f'  <rect x="{gx}" y="{gy - 8}" width="9" height="9" fill="{inks[i]}"/>')
        label = f"{name} {pct:.1f}%"
        draw(lg, label, gx + 15, gy, muted)
        gx += 15 + lg.measure(label) + 22

    grain = "0.16" if dark else "0.2"
    body = "\n".join(out)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Live public GitHub signals for {LOGIN}: {s['total']} contributions in the last 52 weeks across {s['repos']} public repositories">
  <defs>
    <filter id="gs" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.7 0.7 0.7 0 -0.55"/>
    </filter>
  </defs>
  <rect width="{W}" height="{H}" fill="{bg}"/>
{body}
  <rect width="{W}" height="{H}" filter="url(#gs)" opacity="{grain}" pointer-events="none"/>
</svg>
'''


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set GITHUB_TOKEN (or GH_TOKEN) in the environment.")
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    data = summarize(fetch())
    open(f"{outdir}/signals.svg", "w").write(build(data, dark=False))
    open(f"{outdir}/signals-dark.svg", "w").write(build(data, dark=True))
    print(
        f"signals: {data['total']:,} contributions · {data['repos']} repos · "
        f"{data['active_days']} active days · busiest {data['best_day']}"
    )
