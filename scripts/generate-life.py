#!/usr/bin/env python3
"""Record Conway Life as two animated SVG paths for a GitHub README.

Match the website's 15 generations/second, five-pixel grid, sharp cyan cells
and moving highlights. No per-cell animations, JavaScript or external services.
The 300-generation recording repeats with a brief fade at its boundary.
"""
from collections import Counter
from pathlib import Path
from random import Random
import xml.etree.ElementTree as ET

WIDTH, HEIGHT = 960, 168
CELL, PIXEL = 5, 3
COLS, ROWS = WIDTH // CELL, HEIGHT // CELL
WORLD_COLS, WORLD_ROWS = COLS + 24, ROWS + 48
CROP_X, CROP_Y = 12, 24
GENERATIONS, GENERATIONS_PER_SECOND = 300, 15


def initial_population():
    rng = Random(72)
    return {(x, y) for y in range(WORLD_ROWS) for x in range(WORLD_COLS)
            if rng.random() < 0.22}


def step(population):
    neighbours = Counter(
        ((x + dx) % WORLD_COLS, (y + dy) % WORLD_ROWS)
        for x, y in population
        for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
    return {cell for cell, count in neighbours.items()
            if count == 3 or (count == 2 and cell in population)}


def visible(population):
    return {(x - CROP_X, y - CROP_Y) for x, y in population
            if CROP_X <= x < CROP_X + COLS and CROP_Y <= y < CROP_Y + ROWS}


def path_data(cells):
    # Each horizontal, three-pixel stroke is exactly a three-pixel square.
    # This is more compact than one closed rectangle per cell.
    return ''.join(f'M{x*CELL+1},{y*CELL+2.5:g}h{PIXEL}'
                   for x, y in sorted(cells, key=lambda p: (p[1], p[0]))) or 'M0,0'


def layer(paths, css_class, duration, extra=''):
    return (f'<path class="{css_class}" d="{paths[0]}"{extra}>'
            '<animate attributeName="d" calcMode="discrete" '
            f'values="{";".join(paths)}" dur="{duration:g}s" repeatCount="indefinite"/>'
            '</path>')


def render():
    population = initial_population()
    base, highlights, frames = [], [], []
    for generation in range(GENERATIONS):
        cells = visible(population)
        frames.append(cells)
        bright = {cell for cell in cells if (sum(cell) + generation) % 7 == 0}
        base.append(path_data(cells))
        highlights.append(path_data(bright))
        population = step(population)
    duration = GENERATIONS / GENERATIONS_PER_SECOND
    svg = '\n'.join([
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'role="img" aria-labelledby="life-title life-description">',
        '<title id="life-title">Conway’s Game of Life</title>',
        '<desc id="life-description">Cyan colonies grow, collide and dissolve '
        'at 15 generations per second. A 20-second recording of 300 genuine '
        'Conway generations, with a brief fade at the repeat boundary.</desc>',
        '<style>.cells{stroke:#00b8aa}.spark{stroke:#00fff0}.still{display:none}'
        '@media(prefers-color-scheme:light){.cells{stroke:#008d84}.spark{stroke:#00655e}}'
        '@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',
        '<defs><filter id="halo" x="-10%" y="-10%" width="120%" height="120%" '
        'color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="1.2"/>'
        '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<g fill="none" stroke-width="{PIXEL}" stroke-linecap="butt">',
        f'<g class="still"><path class="cells" d="{base[20]}"/>'
        f'<path class="spark" d="{highlights[20]}"/></g>',
        '<g class="motion">',
        f'<animate attributeName="opacity" values="0;1;1;0" '
        f'keyTimes="0;{0.12/duration:g};{1-0.12/duration:g};1" '
        f'dur="{duration:g}s" repeatCount="indefinite"/>',
        layer(base, 'cells', duration),
        layer(highlights, 'spark', duration, ' filter="url(#halo)"'),
        '</g></g></svg>', '',
    ])
    ET.fromstring(svg)
    activity = [len(left ^ right) for left, right in zip(frames, frames[1:])]
    print(f'{GENERATIONS_PER_SECOND} generations/s; {GENERATIONS} frames / {duration:g}s; '
          f'2 animated paths; late activity {sum(activity[-50:])//50} cells/generation; '
          f'{len(svg.encode())//1024} KiB')
    return svg


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[1] / 'assets' / 'life.svg'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(), encoding='utf-8')
