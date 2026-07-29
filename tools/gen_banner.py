"""Generate the paolosand profile README banner (light + dark) as pure SVG paths."""
import os
import sys
from text2path import Typesetter

HERE = os.path.dirname(os.path.abspath(__file__))
JBM = os.path.join(HERE, "fonts", "JetBrainsMono-ExtraBold.ttf")
JBM_MED = os.path.join(HERE, "fonts", "JetBrainsMono-Medium.ttf")

W, H = 960, 260
PAD = 64

INK = "#1A130A"
PAPER = "#F2EBDA"
PINK = "#F0457B"
BLUE = "#2841E8"
LEMON = "#E8B91A"
MINT = "#00A076"


def build(dark: bool) -> str:
    bg = INK if dark else PAPER
    fg = PAPER if dark else INK
    muted = "#8C7F63" if dark else "#7A6C53"
    faint = "#5C523E" if dark else "#B6A988"
    rule = "#3A3226" if dark else "#DDD2B5"
    # riso blue is too dim against near-black ink; lift it for the dark variant only
    blue = "#5C72F2" if dark else BLUE

    # ---- wordmark: paolo. / sandejas/  (hero spec: 800 weight, -0.05em tracking, 0.88 lh)
    size = 104
    ts = Typesetter(JBM, size, tracking_em=-0.05)
    lh = size * 0.88

    y1 = 108
    y2 = y1 + lh

    line1, _ = ts.run_paths([("paolo", fg), (".", PINK)], PAD, y1)
    line2, _ = ts.run_paths([("sande", fg), ("jas", blue), ("/", LEMON)], PAD, y2)

    wordmark = "\n".join(
        f'  <path d="{d}" fill="{c}"/>' for d, c in (line1 + line2)
    )

    # ---- right column: small tracked mono metadata, also as paths
    ms = Typesetter(JBM_MED, 11.5, tracking_em=0.18)
    col_x = 660
    meta = []

    rows = [
        ("AI / ML ENGINEER", fg, 0),
        ("CREATIVE TECHNOLOGIST", fg, 18),
        (None, None, 34),  # rule
        ("CALARTS MFA '26 · 4.0", muted, 52),
        ("UP DILIMAN CS '23", muted, 70),
        ("LOS ANGELES, CA", muted, 88),
    ]
    base_y = 90
    for text, color, dy in rows:
        if text is None:
            meta.append(
                f'  <line x1="{col_x}" y1="{base_y + dy}" x2="{W - PAD}" y2="{base_y + dy}" '
                f'stroke="{rule}" stroke-width="1" stroke-dasharray="2 4"/>'
            )
            continue
        paths, _ = ms.run_paths([(text, color)], col_x, base_y + dy)
        for d, c in paths:
            meta.append(f'  <path d="{d}" fill="{c}"/>')

    # small mint status dot next to the availability line
    meta.append(f'  <circle cx="{col_x - 14}" cy="{base_y + 84}" r="3.5" fill="{MINT}"/>')

    metadata = "\n".join(meta)

    # The wordmark already carries pink/blue/lemon and the status dot is mint,
    # so the four-ink system is fully present without a separate swatch strip.
    inks = ""

    grain_op = "0.16" if dark else "0.2"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Paolo Sandejas — AI/ML Engineer and Creative Technologist">
  <defs>
    <filter id="g" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.7 0.7 0.7 0 -0.55"/>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" fill="{bg}"/>

{wordmark}

{metadata}

{inks}
  <rect width="{W}" height="{H}" filter="url(#g)" opacity="{grain_op}" pointer-events="none"/>
</svg>
'''


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    open(f"{out}/banner.svg", "w").write(build(dark=False))
    open(f"{out}/banner-dark.svg", "w").write(build(dark=True))
    print("wrote banner.svg + banner-dark.svg")
