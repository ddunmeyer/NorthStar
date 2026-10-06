"""The North Star banner: an aurora over a snow-capped range and a still lake.

Drawn procedurally as one SVG so the app ships no stock imagery. Everything is
seeded, so the picture is identical on every run and every machine.

The scene is 1600 x 400 units. The lake's far shore is at y = SHORE.
"""
from __future__ import annotations

import base64
import math
import random
from functools import lru_cache

W, H, SHORE = 1600, 400, 276
MIDNIGHT = "#0C1626"


def _noise(seed: int, knots: int):
    """Smooth 1-D value noise on [0, 1]: random knots joined with cosine easing."""
    rng = random.Random(seed)
    values = [rng.random() for _ in range(knots + 2)]

    def at(t: float) -> float:
        x = max(0.0, min(1.0, t)) * knots
        i = int(x)
        f = (1 - math.cos((x - i) * math.pi)) / 2
        return values[i] * (1 - f) + values[i + 1] * f

    return at


def _fractal(seed: int, knots: int, octaves: int = 4):
    """Layered noise: each octave doubles the detail and halves the strength."""
    layers = [(_noise(seed + o * 17, knots * 2 ** o), 0.5 ** o) for o in range(octaves)]
    total = sum(weight for _, weight in layers)
    return lambda t: sum(f(t) * weight for f, weight in layers) / total


# ---------------------------------------------------------------- mountains
def _ridge(seed: int, peaks: list[tuple[float, float, float]], height: float, step: int = 5) -> list[tuple[int, float]]:
    """A ridgeline as (x, y) points. peaks are (x, relative height, half-width)."""
    swell, crag = _fractal(seed, 9), _fractal(seed + 5, 70, 3)
    points = []
    for x in range(-20, W + 21, step):
        t = (x + 20) / (W + 40)
        # Pointed peaks with concave flanks; the highest one at each x wins.
        lift = max(h * max(0.0, 1 - abs(x - px) / w) ** 1.3 for px, h, w in peaks)
        elevation = max(lift, 0.14) * (0.8 + 0.3 * swell(t)) + 0.055 * (crag(t) - 0.5) * (0.4 + lift)
        points.append((x, SHORE - height * elevation))
    return points


def _path(points: list[tuple[float, float]]) -> str:
    return "M" + " L".join(f"{x:.0f} {y:.1f}" for x, y in points)


def _snow(points: list[tuple[int, float]], seed: int, height: float, reach: float) -> str:
    """Snow from each summit down to a ragged line, deeper on the higher ground."""
    ragged, n = _fractal(seed, 110, 3), len(points)
    lower = []
    for i, (x, y) in enumerate(points):
        elevation = (SHORE - y) / height
        cover = max(0.0, min(1.0, (elevation - 0.4) / 0.35))
        lower.append((x, y + reach * cover * (0.25 + 1.3 * ragged(i / n))))
    return _path(points + lower[::-1]) + "Z"


def _shadows(points: list[tuple[int, float]], peaks: list[tuple[float, float, float]], seed: int) -> str:
    """The side of each peak facing away from the light, with a broken edge like a rock spur."""
    rng, faces = random.Random(seed), []

    def descend(x: float, y: float, drift: tuple[float, float]) -> list[tuple[float, float]]:
        line = []
        while y < SHORE:
            y += rng.uniform(9, 20)
            x += rng.uniform(*drift)
            line.append((x, min(y, SHORE)))
        return line

    for px, _, w in peaks:
        slope = [(x, y) for x, y in points if px <= x <= px + w]
        if len(slope) < 4:
            continue
        # Follow the ridge down from the summit until it starts climbing the next peak.
        valley = max(range(len(slope)), key=lambda i: slope[i][1])
        on_ridge = slope[: max(valley, 3) + 1]
        spur = descend(*on_ridge[0], drift=(-7, 12))
        gully = descend(*on_ridge[-1], drift=(-11, 5))
        faces.append(_path(on_ridge + gully + spur[::-1]) + "Z")
    return " ".join(faces)


def _range(name: str, seed: int, peaks, height: float, top: str, bottom: str, snow_reach: float,
           snow_opacity: float, shadow_opacity: float) -> tuple[str, str]:
    """One mountain range. Returns (defs, drawing)."""
    points = _ridge(seed, peaks, height)
    outline = _path(points) + f" L{W + 20} {SHORE} L-20 {SHORE}Z"
    defs = (f'<clipPath id="{name}"><path d="{outline}"/></clipPath>'
            f'<linearGradient id="{name}-fill" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>')
    drawing = (
        f'<path id="{name}-shape" d="{outline}" fill="url(#{name}-fill)"/>'
        f'<g clip-path="url(#{name})">'
        f'<path d="{_snow(points, seed + 3, height, snow_reach)}" fill="url(#snow)" opacity="{snow_opacity}"/>'
        f'<path d="{_shadows(points, peaks, seed + 9)}" fill="#050E1C" opacity="{shadow_opacity}"/>'
        f'<rect width="{W}" height="{SHORE}" filter="url(#rock)" opacity=".3"/>'
        f'<rect width="{W}" height="{SHORE}" fill="url(#auroralight)"/>'
        f'<rect y="{SHORE - 70}" width="{W}" height="70" fill="url(#mist)"/></g>'
    )
    return defs, drawing


def _forest(seed: int) -> str:
    """A dark line of conifers along the shore."""
    rng, tall = random.Random(seed), _fractal(seed, 14)
    points, x = [(-20.0, float(SHORE))], -20.0
    while x < W + 20:
        size = 5 + 17 * tall((x + 20) / (W + 40)) * rng.uniform(0.6, 1.2)
        width = rng.uniform(5, 9)
        points += [(x + width / 2, SHORE - size), (x + width, SHORE - size * rng.uniform(0.1, 0.35))]
        x += width
    return _path(points) + f" L{W + 20} {SHORE + 3} L-20 {SHORE + 3}Z"


# ------------------------------------------------------------------- aurora
def _curtain(seed: int, x0: int, x1: int, base: float, sway: float, period: float, height: float,
             strength: float) -> str:
    """One aurora curtain: hundreds of vertical rays hanging from a wavy lower edge."""
    span = x1 - x0
    tall, bright = _fractal(seed, max(4, span // 150), 3), _fractal(seed + 1, max(8, span // 34), 4)
    rays = []
    for x in range(x0, x1, 6):
        t = (x - x0) / span
        foot = base + sway * math.sin(x / period + seed) + sway * 0.4 * math.sin(x / (period * 0.37) + seed * 2)
        ends = min(1.0, t / 0.14, (1 - t) / 0.14)  # fade out toward both ends of the curtain
        rise = height * (0.4 + 0.8 * tall(t))
        glow = strength * ends * (0.12 + 0.88 * bright(t) ** 1.6)
        rays.append(f'<rect x="{x}" y="{foot - rise:.0f}" width="7" height="{rise:.0f}" opacity="{glow:.2f}"/>')
    return "".join(rays)


def _stars(seed: int) -> str:
    rng, out = random.Random(seed), []
    for _ in range(300):
        x, y = rng.uniform(0, W), rng.uniform(0, 230) ** 1.0
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice([.5, .6, .7, .8, 1.0]):.1f}" '
                   f'fill="#fff" opacity="{rng.uniform(.2, .9):.2f}"/>')
    for _ in range(14):
        x, y = rng.uniform(0, W), rng.uniform(4, 170)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="#CFE6FF" opacity=".1"/>'
                   f'<circle cx="{x:.0f}" cy="{y:.0f}" r="1.4" fill="#fff"/>')
    return "".join(out)


def _north_star(x: float, y: float) -> str:
    """The star the product is named for: bright, with four fine diffraction spikes."""
    return (f'<g transform="translate({x} {y})">'
            '<circle r="26" fill="url(#halo)"/>'
            '<path d="M0 -30 L1.6 -1.6 L30 0 L1.6 1.6 L0 30 L-1.6 1.6 L-30 0 L-1.6 -1.6Z" fill="#EAF6FF" opacity=".9"/>'
            '<path d="M0 -9 L2.6 -2.6 L9 0 L2.6 2.6 L0 9 L-2.6 2.6 L-9 0 L-2.6 -2.6Z" fill="#fff"/></g>')


@lru_cache(maxsize=1)
def banner_svg() -> str:
    far_defs, far = _range("far", 21, [(110, .46, 170), (350, .55, 190), (640, .9, 230), (860, .6, 180),
                                        (1030, 1.0, 250), (1270, .74, 200), (1450, .88, 210), (1600, .6, 170)],
                           height=198, top="#3B5B84", bottom="#1A3352", snow_reach=64, snow_opacity=.92,
                           shadow_opacity=.42)
    mid_defs, mid = _range("mid", 48, [(30, .7, 150), (240, .86, 170), (470, .6, 150), (770, .82, 190),
                                        (1140, .76, 180), (1350, 1.0, 190), (1550, .7, 160)],
                           height=112, top="#223F62", bottom="#0E2138", snow_reach=26, snow_opacity=.55,
                           shadow_opacity=.5)
    back = _curtain(3, 560, 1640, 118, 20, 150, 150, .8)
    front = _curtain(8, 800, 1640, 174, 30, 120, 200, 1.0)
    wisp = _curtain(14, 120, 900, 96, 14, 170, 110, .36)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#030712"/><stop offset=".45" stop-color="#081A33"/><stop offset=".69" stop-color="#12344F"/>
 </linearGradient>
 <linearGradient id="ray" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#7C6CFF" stop-opacity="0"/><stop offset=".2" stop-color="#6F7CFF" stop-opacity=".3"/>
  <stop offset=".5" stop-color="#2FE0A0" stop-opacity=".55"/><stop offset=".9" stop-color="#9BFFD6" stop-opacity="1"/>
  <stop offset="1" stop-color="#D8FFF0" stop-opacity="0"/>
 </linearGradient>
 <linearGradient id="snow" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#F4FAFF"/><stop offset="1" stop-color="#A9C4E6"/>
 </linearGradient>
 <linearGradient id="mist" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2B5876" stop-opacity="0"/><stop offset="1" stop-color="#2B5876" stop-opacity=".55"/>
 </linearGradient>
 <radialGradient id="auroralight" cx="1180" cy="60" r="760" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#3CFFB0" stop-opacity=".2"/><stop offset="1" stop-color="#3CFFB0" stop-opacity="0"/>
 </radialGradient>
 <radialGradient id="halo"><stop offset="0" stop-color="#CFE9FF" stop-opacity=".55"/><stop offset="1" stop-color="#CFE9FF" stop-opacity="0"/></radialGradient>
 <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#0E2B45"/><stop offset=".55" stop-color="#0B1B30"/><stop offset="1" stop-color="{MIDNIGHT}"/>
 </linearGradient>
 <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
  <stop offset=".72" stop-color="{MIDNIGHT}" stop-opacity="0"/><stop offset=".98" stop-color="{MIDNIGHT}"/>
 </linearGradient>
 <linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{MIDNIGHT}" stop-opacity=".78"/><stop offset=".3" stop-color="{MIDNIGHT}" stop-opacity=".4"/>
  <stop offset=".55" stop-color="{MIDNIGHT}" stop-opacity="0"/>
 </linearGradient>
 <filter id="streak" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="1.7 1"/></filter>
 <filter id="bloom" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="30"/></filter>
 <filter id="ripple" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="14 3"/></filter>
 <filter id="soften"><feGaussianBlur stdDeviation="2.5 1"/></filter>
 <filter id="rock" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".075 .011" numOctaves="3" seed="4"/>
  <feColorMatrix values="0 0 0 0 .02  0 0 0 0 .06  0 0 0 0 .12  1.9 0 0 0 -.78"/>
 </filter>
 <clipPath id="lake"><rect y="{SHORE}" width="{W}" height="{H - SHORE}"/></clipPath>
 <g id="aurora" fill="url(#ray)" transform="skewX(-11) translate(52 0)">
  <g opacity=".8">{back}</g><g>{front}</g><g>{wisp}</g>
 </g>
 {far_defs}{mid_defs}
</defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{_stars(5)}
{_north_star(418, 54)}
<use xlink:href="#aurora" href="#aurora" filter="url(#bloom)" opacity=".7"/>
<use xlink:href="#aurora" href="#aurora" filter="url(#streak)"/>
{far}
{mid}
<path d="{_forest(77)}" fill="#06101D"/>
<rect y="{SHORE}" width="{W}" height="{H - SHORE}" fill="url(#water)"/>
<g clip-path="url(#lake)">
 <g transform="matrix(1 0 0 -.62 0 {SHORE * 1.62:.0f})" opacity=".34" filter="url(#soften)">
  <use xlink:href="#far-shape" href="#far-shape"/><use xlink:href="#mid-shape" href="#mid-shape"/>
 </g>
 <g transform="matrix(1 0 0 -.5 0 {SHORE * 1.5:.0f})" opacity=".5" filter="url(#ripple)"><use xlink:href="#aurora" href="#aurora"/></g>
 <rect y="{SHORE}" width="{W}" height="2" fill="#7FD9C4" opacity=".16"/>
</g>
<rect width="{W}" height="{H}" fill="url(#shade)"/>
<rect width="{W}" height="{H}" fill="url(#fade)"/>
</svg>"""


def banner_data_uri() -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(banner_svg().encode()).decode()
