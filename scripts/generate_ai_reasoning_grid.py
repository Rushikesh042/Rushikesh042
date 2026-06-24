#!/usr/bin/env python3
"""Generate a self-contained animated AI reasoning grid SVG."""

import os

TEAL = "#2dd4bf"
GREEN = "#22c55e"
BLUE = "#3b82f6"
PURPLE = "#8b5cf6"
ORANGE = "#f97316"
WHITE = "#ffffff"

THEMES = {
    "light": {
        "panel": "#ffffff",
        "hidden": "#e8edf3",
        "edge": "#cfd8e3",
        "label": "#475569",
        "revealed": "#eefcf9",
    },
    "dark": {
        "panel": "#0d1117",
        "hidden": "#1f2937",
        "edge": "#334155",
        "label": "#94a3b8",
        "revealed": "#102a2a",
    },
}

W = 820
DURATION = 16.0
COLS, ROWS = 20, 7
TILE, GAP = 30, 5
PITCH = TILE + GAP
GRID_W = COLS * PITCH - GAP
GRID_H = ROWS * PITCH - GAP
SX = (W - GRID_W) // 2
SY = 64
BOTTOM_PAD = 50
H = SY + GRID_H + BOTTOM_PAD

RISKS = {
    (2, 1), (4, 5), (6, 2), (7, 6), (9, 1),
    (11, 4), (13, 2), (14, 5), (16, 1), (16, 6),
}

PATH = [
    (0, 3), (1, 3), (2, 3), (3, 3), (3, 2),
    (4, 2), (5, 2), (5, 3), (6, 3), (7, 3),
    (8, 3), (8, 2), (9, 2), (10, 2), (10, 3),
    (11, 3), (12, 3), (12, 2), (13, 3), (14, 3),
    (15, 3), (15, 4), (16, 4), (17, 3),
]

OUTPUT = (17, 3)

NUM_COLOURS = {
    0: TEAL,
    1: BLUE,
    2: GREEN,
    3: PURPLE,
    4: ORANGE,
    5: ORANGE,
}


def in_grid(cell):
    c, r = cell
    return 0 <= c < COLS and 0 <= r < ROWS


def neighbours(cell):
    c, r = cell
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue

            nb = c + dc, r + dr
            if in_grid(nb):
                yield nb


def risk_count(cell):
    return sum(1 for nb in neighbours(cell) if nb in RISKS)


def tile_xy(cell):
    c, r = cell
    return SX + c * PITCH, SY + r * PITCH


def tile_center(cell):
    x, y = tile_xy(cell)
    return x + TILE / 2, y + TILE / 2


def escape_attr(value):
    return str(value).replace("&", "&amp;").replace('"', "&quot;")


def reveal_schedule():
    reveals = {}

    for index, cell in enumerate(PATH):
        t = 0.08 + 0.66 * index / (len(PATH) - 1)

        if cell not in RISKS:
            reveals[cell] = min(reveals.get(cell, 1), t)

        if risk_count(cell) == 0:
            for nb in neighbours(cell):
                if nb not in RISKS:
                    reveals[nb] = min(reveals.get(nb, 1), t + 0.035)

    extra_cells = [
        (0, 2), (1, 2), (2, 4), (4, 3), (6, 4),
        (9, 3), (12, 4), (14, 2), (15, 2),
    ]

    for cell in extra_cells:
        if cell not in RISKS:
            reveals[cell] = min(reveals.get(cell, 1), 0.18 + (cell[0] % 6) * 0.08)

    return dict(sorted(reveals.items(), key=lambda item: item[1]))


def fade_key_times(start, hold_until=0.92, end=0.96):
    return f"0;{start:.3f};{min(start + 0.025, 0.90):.3f};{hold_until:.3f};{end:.3f};1"


def reveal_tile(cell, start, theme):
    x, y = tile_xy(cell)
    number = risk_count(cell)
    colour = NUM_COLOURS.get(number, PURPLE)
    fill = theme["revealed"] if number == 0 else colour
    text = "·" if number == 0 else str(number)
    text_colour = colour if number == 0 else WHITE
    key_times = fade_key_times(start)

    return f'''
  <g transform="translate({x + TILE / 2:.1f},{y + TILE / 2:.1f})" opacity="0">
    <animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="{key_times}"/>
    <g>
      <animateTransform attributeName="transform" type="scale" dur="{DURATION}s" repeatCount="indefinite" values="0.15 1;0.15 1;1 1;1 1;0.15 1;0.15 1" keyTimes="{key_times}"/>
      <rect x="{-TILE / 2}" y="{-TILE / 2}" width="{TILE}" height="{TILE}" rx="6" fill="{fill}" opacity="{0.34 if number == 0 else 0.86}"/>
      <rect x="{-TILE / 2}" y="{-TILE / 2}" width="{TILE}" height="{TILE}" rx="6" fill="none" stroke="{colour}" stroke-width="1.4" opacity="0.72"/>
      <text x="0" y="1" text-anchor="middle" dominant-baseline="middle" class="num" fill="{text_colour}" font-size="{16 if number else 19}">{text}</text>
    </g>
  </g>'''


def risk_flag(cell, start):
    x, y = tile_xy(cell)
    colour = ORANGE if (cell[0] + cell[1]) % 2 else PURPLE
    key_times = fade_key_times(start, 0.94, 0.97)

    return f'''
  <g transform="translate({x + TILE / 2:.1f},{y + TILE / 2:.1f})" opacity="0" filter="url(#softGlow)">
    <animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="{key_times}"/>
    <rect x="{-TILE / 2}" y="{-TILE / 2}" width="{TILE}" height="{TILE}" rx="6" fill="{colour}" opacity="0.20"/>
    <rect x="{-TILE / 2}" y="{-TILE / 2}" width="{TILE}" height="{TILE}" rx="6" fill="none" stroke="{colour}" stroke-width="1.4"/>
    <line x1="-5" y1="-10" x2="-5" y2="12" stroke="{colour}" stroke-width="2" stroke-linecap="round"/>
    <path d="M-5 -10 L10 -5 L-5 0 Z" fill="{colour}"/>
    <animateTransform attributeName="transform" type="scale" additive="sum" dur="1.4s" begin="{start * DURATION:.2f}s" repeatCount="indefinite" values="1;1.08;1" keyTimes="0;0.5;1"/>
  </g>'''


def output_tile():
    x, y = tile_xy(OUTPUT)
    start = 0.82
    key_times = fade_key_times(start, 0.94, 0.97)

    return f'''
  <g transform="translate({x + TILE / 2:.1f},{y + TILE / 2:.1f})" opacity="0" filter="url(#strongGlow)">
    <animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="{key_times}"/>
    <circle r="19" fill="none" stroke="{TEAL}" stroke-width="2">
      <animate attributeName="r" dur="1.7s" begin="{start * DURATION:.2f}s" repeatCount="indefinite" values="19;38;19" keyTimes="0;1;1"/>
      <animate attributeName="opacity" dur="1.7s" begin="{start * DURATION:.2f}s" repeatCount="indefinite" values="0.85;0;0" keyTimes="0;1;1"/>
    </circle>
    <rect x="{-TILE / 2}" y="{-TILE / 2}" width="{TILE}" height="{TILE}" rx="6" fill="{TEAL}"/>
    <text x="0" y="1" text-anchor="middle" dominant-baseline="middle" class="num" fill="{WHITE}" font-size="17">AI</text>
  </g>'''


def score_text():
    values = ["000", "060", "140", "260", "390", "520", "700", "880"]
    chunks = []

    for index, value in enumerate(values):
        start = 0.06 + index * 0.095
        stop = start + 0.11

        chunks.append(f'''
    <text x="160" y="40" class="score" opacity="0">{value}
      <animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" values="0;1;1;0" keyTimes="0;{start:.3f};{stop:.3f};{min(stop + 0.02, 0.98):.3f}"/>
    </text>''')

    return "".join(chunks)


def cursor_path():
    points = [tile_center(cell) for cell in PATH]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)


def build_svg(theme):
    reveals = reveal_schedule()
    risk_times = {
        cell: 0.20 + 0.52 * index / max(len(RISKS) - 1, 1)
        for index, cell in enumerate(sorted(RISKS))
    }

    path = cursor_path()
    panel_x = SX - 26
    panel_y = 32
    panel_w = GRID_W + 52
    panel_h = GRID_H + 76

    parts = [f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg" overflow="visible" role="img" aria-label="Animated Minesweeper-style AI reasoning grid">  <defs>
    <filter id="softGlow" x="-120%" y="-120%" width="340%" height="340%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="strongGlow" x="-180%" y="-180%" width="460%" height="460%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .label {{ fill: {theme['label']}; font-family: "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; letter-spacing: 5px; font-weight: 700; }}
    .score {{ fill: {TEAL}; font-family: "Consolas", "SF Mono", Menlo, monospace; font-size: 16px; font-weight: 800; }}
    .num {{ font-family: "Consolas", "SF Mono", Menlo, monospace; font-weight: 800; }}
  </style>

  <rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" rx="18" fill="{theme['panel']}" opacity="0.02" stroke="{theme['edge']}" stroke-width="1.2"/>

  <text x="{SX}" y="40" class="label">SCORE</text>
  {score_text()}

  <text x="{SX + GRID_W - 220}" y="40" class="label">CONFIDENCE</text>
  <rect x="{SX + GRID_W - 84}" y="30" width="84" height="10" rx="5" fill="none" stroke="{theme['edge']}" stroke-width="1.2"/>
  <rect x="{SX + GRID_W - 84}" y="30" width="0" height="10" rx="5" fill="{TEAL}" opacity="0.85">
    <animate attributeName="width" dur="{DURATION}s" repeatCount="indefinite" values="0;18;42;66;84;84;0" keyTimes="0;0.18;0.38;0.60;0.82;0.94;1"/>
  </rect>
''']

    parts.append('  <g>')
    for r in range(ROWS):
        for c in range(COLS):
            x, y = tile_xy((c, r))
            parts.append(
                f'    <rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="6" fill="{theme["hidden"]}" stroke="{theme["edge"]}" stroke-width="1.2"/>'
            )
    parts.append('  </g>')

    for cell, start in reveals.items():
        if cell != OUTPUT:
            parts.append(reveal_tile(cell, start, theme))

    for cell, start in risk_times.items():
        parts.append(risk_flag(cell, start))

    parts.append(output_tile())

    parts.append(f'''
  <g filter="url(#strongGlow)">
    <circle r="15" fill="{TEAL}" opacity="0.18"/>
    <rect x="-12" y="-12" width="24" height="24" rx="7" fill="{theme['panel']}" stroke="{TEAL}" stroke-width="2.2"/>
    <path d="M-5 0 H5 M0 -5 V5" stroke="{TEAL}" stroke-width="2.2" stroke-linecap="round"/>
    <circle r="3" fill="{TEAL}">
      <animate attributeName="r" dur="1.1s" repeatCount="indefinite" values="2.2;3.8;2.2" keyTimes="0;0.5;1"/>
    </circle>
    <animateMotion dur="{DURATION}s" repeatCount="indefinite" path="{escape_attr(path)}" rotate="0"/>
  </g>
''')

    label_y = SY + GRID_H + 34
    labels = [("DATA", 0.06), ("REASON", 0.34), ("VERIFY", 0.66), ("OUTPUT", 0.94)]

    for label, factor in labels:
        parts.append(
            f'  <text x="{SX + GRID_W * factor:.0f}" y="{label_y}" text-anchor="middle" class="label">{label}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
    os.makedirs(out_dir, exist_ok=True)

    targets = {
        "ai-reasoning-grid.svg": THEMES["light"],
        "ai-reasoning-grid-dark.svg": THEMES["dark"],
    }

    for name, theme in targets.items():
        path = os.path.join(out_dir, name)

        with open(path, "w", encoding="utf-8") as f:
            f.write(build_svg(theme))

        print(f"wrote {path}")


if __name__ == "__main__":
    main()
