#!/usr/bin/env python3
"""
Generate the neofetch-style info card that sits to the RIGHT of meet-ascii.svg
(art left, specs right -- the classic neofetch layout).

Canvas is 840 x 880, the same as the portrait, so equal-width table cells give
identical heights. The README shows it at ~half size, so fonts are ~2x what
they'd be at full width.

The "Uptime" row reads live numbers from data/contributions.json, so the card
is re-rendered by the daily workflow alongside the heatmap and stats.

    python scripts/make_info_card.py [data.json] [output.svg]
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "info-card.svg")

W, H = 840, 880
PAD = 32
TITLEBAR_H = 30
FONT = 25
ROW_STEP = 47
KEY_W = 10            # key column width in characters
CHAR_W = FONT * 0.6   # monospace advance

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
CYAN = "#22d3ee"
GREEN = "#39d353"
YELLOW = "#f2cc60"
BLUE = "#58a6ff"
MAGENTA = "#bc8cff"
RED = "#ff7b72"

try:
    data = json.load(open(SRC))
    streak = data.get("current_streak", {}).get("length", 0)
    total = data.get("total_contributions", 0)
    uptime = f"{streak}-day streak · {total:,} contribs/yr"
except Exception:
    uptime = "always shipping"

INFO_ROWS = [
    ("Role", "Full-Stack & AI/ML Engineer", INK),
    ("Study", "B.Tech CSE (Data Science)", INK),
    ("Uptime", uptime, GREEN),
    ("Shell", "zsh · macOS / Ubuntu", INK),
    ("Langs", "Python, TypeScript, JS, C++", BLUE),
    ("Backend", "FastAPI, Node, Express, Django", CYAN),
    ("Frontend", "React, Next.js, Tailwind, Vite", CYAN),
    ("AI / ML", "LLM apps, RAG, YOLOv8, sklearn", MAGENTA),
    ("Data", "PostgreSQL, MongoDB, Drizzle", INK),
    ("DevOps", "Docker, AWS, Vercel, Actions", YELLOW),
    ("Shipping", "Hooky · Clippin · VibeCheck", GREEN),
    ("Status", "Open to internships & collabs", CYAN),
]

SWATCHES = ["#21262d", RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, INK]


def row(y, delay, inner):
    return f'<g class="l" style="animation-delay:{delay:.2f}s"><text x="{PAD}" y="{y}" font-size="{FONT}">{inner}</text></g>'


def render():
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>'
        '.l{opacity:0;animation:in .4s ease-out both}'
        '@keyframes in{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}'
        '@media (prefers-reduced-motion: reduce){.l{opacity:1!important;transform:none!important;animation:none!important}}'
        '</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{20 + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">meet@github: ~$ neofetch</text>')

    y = TITLEBAR_H + 64
    delay = 0.1
    p.append(row(y, delay, f'<tspan fill="{CYAN}" font-weight="700">meet</tspan><tspan fill="{MUTED}">@</tspan>'
                           f'<tspan fill="{GREEN}" font-weight="700">github</tspan>'))
    y += 34
    delay += 0.05
    p.append(row(y, delay, f'<tspan fill="{FRAME}">{"─" * 14}</tspan>'))

    for key, val, color in INFO_ROWS:
        y += ROW_STEP
        delay += 0.06
        p.append(row(y, delay,
                     f'<tspan fill="{YELLOW}" font-weight="700">{html.escape(key)}</tspan>'
                     f'<tspan x="{PAD + KEY_W * CHAR_W:.0f}" fill="{MUTED}">: </tspan>'
                     f'<tspan fill="{color}">{html.escape(val)}</tspan>'))

    y += 44
    delay += 0.08
    size, gap = 40, 10
    p.append(f'<g class="l" style="animation-delay:{delay:.2f}s">')
    for i, col in enumerate(SWATCHES):
        p.append(f'<rect x="{PAD + i * (size + gap)}" y="{y}" width="{size}" height="{size // 2}" rx="4" fill="{col}"/>')
    p.append('</g>')

    y += 76
    delay += 0.08
    prompt = "meet@github:~$ "
    p.append(f'<g class="l" style="animation-delay:{delay:.2f}s">'
             f'<text x="{PAD}" y="{y}" font-size="{FONT}"><tspan fill="{GREEN}">meet@github</tspan>'
             f'<tspan fill="{MUTED}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{MUTED}">$ </tspan></text>'
             f'<rect x="{PAD + len(prompt) * CHAR_W:.0f}" y="{y - FONT + 4}" width="{CHAR_W:.0f}" height="{FONT}" fill="{CYAN}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
             f'</rect></g>')

    p.append('</svg>')
    return "".join(p)


if __name__ == "__main__":
    svg = render()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB")
