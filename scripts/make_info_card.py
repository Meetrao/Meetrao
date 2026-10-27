#!/usr/bin/env python3
"""
Generate a Neofetch-style terminal info card SVG for Meet Rao.
Dimensions: 840 x 880 (matches meet-ascii.svg and stats.svg exactly).
Features staggered slide-in animations and terminal color palette swatches.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

W, H = 840, 880
PAD = 24
TITLEBAR_H = 32

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
CYAN = "#22d3ee"
GREEN = "#39d353"
YELLOW = "#f2cc60"
RED = "#ff5f56"
BLUE = "#58a6ff"
MAGENTA = "#bc8cff"

INFO_ROWS = [
    ("OS", "macOS Sonoma / Ubuntu 24.04 LTS", CYAN),
    ("Host", "Meet Rao (Full-Stack & AI/ML Engineer)", INK),
    ("Education", "B.Tech in CSE (Data Science)", INK),
    ("Kernel", "Building & Breaking Scalable Systems", YELLOW),
    ("Uptime", "21 Public Repos · 320+ Contributions", GREEN),
    ("Shell", "zsh / bash (Unix Environment)", INK),
    ("Languages", "Python, JavaScript, C++, SQL", BLUE),
    ("Backend", "FastAPI, Express.js, Django, Node.js", CYAN),
    ("AI / ML", "TensorFlow, scikit-learn, BERT, YOLOv8, LSTM", MAGENTA),
    ("Databases", "PostgreSQL, MongoDB", INK),
    ("Cloud & Tools", "Docker, AWS, Git, GitHub Actions", YELLOW),
    ("Featured", "CargoIntel (YOLOv8) · VoteChain (Blockchain+AI)", GREEN),
    ("Status", "Open to Internships & Collaborations", CYAN),
]

COLOR_SWATCHES = [
    "#21262d", "#ff5f56", "#39d353", "#f2cc60",
    "#58a6ff", "#bc8cff", "#22d3ee", "#e6edf3"
]


def render():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>'
        '.line { opacity: 0; animation: fadeIn 0.4s ease-out both; }'
        '@keyframes fadeIn { 0% { opacity: 0; transform: translateY(8px); } 100% { opacity: 1; transform: translateY(0); } }'
        '@media (prefers-reduced-motion: reduce) { .line { opacity: 1 !important; transform: none !important; animation: none !important; } }'
        '</style>',
        '<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient>'
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    # Titlebar dots
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')

    parts.append(
        f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">meet@github: ~$ neofetch</text>'
    )

    # Main Neofetch Header
    y_cursor = TITLEBAR_H + 38
    delay = 0.05
    parts.append(
        f'<g class="line" style="animation-delay:{delay:.2f}s">'
        f'<text x="{PAD}" y="{y_cursor}" font-size="20" font-weight="700">'
        f'<tspan fill="{CYAN}">meet</tspan><tspan fill="{MUTED}">@</tspan><tspan fill="{GREEN}">github</tspan>'
        f'</text></g>'
    )

    y_cursor += 16
    delay += 0.04
    parts.append(
        f'<g class="line" style="animation-delay:{delay:.2f}s">'
        f'<text x="{PAD}" y="{y_cursor}" fill="{MUTED}" font-size="16">'
        f'-----------------------------------------'
        f'</text></g>'
    )

    # Info Rows
    for key, val, val_color in INFO_ROWS:
        y_cursor += 36
        delay += 0.04
        parts.append(
            f'<g class="line" style="animation-delay:{delay:.2f}s">'
            f'<text x="{PAD}" y="{y_cursor}" font-size="16">'
            f'<tspan fill="{YELLOW}" font-weight="700">{key:14}</tspan>'
            f'<tspan fill="{MUTED}">: </tspan>'
            f'<tspan fill="{val_color}">{val}</tspan>'
            f'</text></g>'
        )

    # Terminal Color Blocks (Palette swatches at bottom)
    y_cursor += 60
    delay += 0.05
    swatch_size = 32
    swatch_gap = 12
    start_x = PAD
    parts.append(f'<g class="line" style="animation-delay:{delay:.2f}s">')
    for i, col in enumerate(COLOR_SWATCHES):
        sx = start_x + i * (swatch_size + swatch_gap)
        parts.append(f'<rect x="{sx}" y="{y_cursor}" width="{swatch_size}" height="{swatch_size}" rx="6" fill="{col}"/>')
    parts.append('</g>')

    # Terminal prompt at bottom with blinking cursor
    y_cursor += 65
    delay += 0.05
    parts.append(
        f'<g class="line" style="animation-delay:{delay:.2f}s">'
        f'<text x="{PAD}" y="{y_cursor}" fill="{MUTED}" font-size="16">'
        f'<tspan fill="{GREEN}">meet@github</tspan><tspan fill="{MUTED}">:</tspan><tspan fill="{BLUE}">~</tspan>'
        f'<tspan fill="{MUTED}">$ </tspan>'
        f'</text>'
        f'<rect x="{PAD + 155}" y="{y_cursor - 15}" width="9" height="18" fill="{CYAN}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
        f'</rect>'
        f'</g>'
    )

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    svg = render()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB")
