"""Convert text runs to SVG path data using JetBrains Mono, preserving per-run color."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform


class Typesetter:
    def __init__(self, path, size, tracking_em=0.0):
        self.font = TTFont(path)
        self.upem = self.font["head"].unitsPerEm
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"]
        self.size = size
        self.scale = size / self.upem
        self.tracking = tracking_em * size  # in final user units

    def _glyph_name(self, ch):
        return self.cmap.get(ord(ch))

    def advance(self, ch):
        gn = self._glyph_name(ch)
        if gn is None:
            return 0
        return self.hmtx[gn][0] * self.scale + self.tracking

    def measure(self, text):
        return sum(self.advance(c) for c in text)

    def run_paths(self, runs, x, y):
        """runs: list of (text, color). Returns list of (d, color) and final x."""
        out = []
        cx = x
        for text, color in runs:
            d_parts = []
            for ch in text:
                gn = self._glyph_name(ch)
                if gn is None:
                    cx += self.advance(ch)
                    continue
                pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.1f}")
                # flip Y (font up is +y, SVG down is +y), scale, translate
                t = Transform(self.scale, 0, 0, -self.scale, cx, y)
                tpen = TransformPen(pen, t)
                self.gs[gn].draw(tpen)
                d = pen.getCommands()
                if d.strip():
                    d_parts.append(d)
                cx += self.advance(ch)
            if d_parts:
                out.append((" ".join(d_parts), color))
        return out, cx
