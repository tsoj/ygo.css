"""Makes the images of ygo.css (assets/).

    python tools/make_assets.py textures   frame and text box textures, from tools/ramps.json
    python tools/make_assets.py wall       the hieroglyph walls, from tools/wall-mask.png
    python tools/make_assets.py frame DIR  the text box frame, from the card templates in DIR
    python tools/make_assets.py ramps DIR  tools/ramps.json, from the card templates in DIR

DIR holds card-<type>.png of kooriookami/yugioh-card
(src/assets/yugioh-card/yugioh/image/). Needs numpy, scipy and Pillow.

Textures: periodic noise (made in the frequency domain, so a tile has no edges), whose
colors follow a ramp: the 256 quantiles of a template's pixels, ordered by brightness. Each
noise value takes the ramp's color at its own quantile, so a texture has the colors and the
contrast of the card. The Dark Synchro ramps were measured on card scans (no template).
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
ASSETS = ROOT / 'assets'

TYPES = ['normal', 'effect', 'ritual', 'fusion', 'synchro', 'xyz', 'link', 'spell', 'trap']
TILE = 512            # tile size of the frame textures; the text textures are half of it
SMALL = TILE // 2

# Regions of a template (1394 x 2031): the plain frame and the inside of the text box
FRAME_REGIONS = [(slice(250, 1490), slice(55, 165)), (slice(250, 1490), slice(1232, 1338)),
                 (slice(250, 370), slice(170, 1225))]
TEXT_REGION = (slice(1545, 1885), slice(125, 1270))


# ---------- noise ----------

def band_noise(beta, low, high, seed):
    # 1/f^beta noise between the frequencies low and high (cycles per pixel), periodic
    fx = np.fft.fftfreq(TILE)[:, None]
    fy = np.fft.fftfreq(TILE)[None, :]
    f = np.maximum(np.hypot(fx, fy), 1e-9)
    amplitude = f ** -beta * np.exp(-(f / high) ** 2) * (1 - np.exp(-(f / low) ** 2))
    phase = np.exp(2j * np.pi * np.random.default_rng(seed).random((TILE, TILE)))
    noise = np.real(np.fft.ifft2(amplitude * phase))
    return noise / noise.std()


def frame_noise():
    # clouds with darker veins between them, as the card frames
    return (band_noise(1.6, 0.008, 0.08, 1) + 0.6 * np.abs(band_noise(1.6, 0.012, 0.08, 11))
            + 0.03 * band_noise(0.8, 0.05, 0.5, 21))


def text_noise():
    # the text box: the same clouds, fainter veins
    return band_noise(1.6, 0.008, 0.08, 3) + 0.3 * np.abs(band_noise(1.6, 0.012, 0.08, 13))


def colored(noise, ramp):
    ramp = np.asarray(ramp, float)
    ranks = np.argsort(np.argsort(noise.ravel())) / (noise.size - 1)
    positions = np.linspace(0, 1, len(ramp))
    rgb = np.stack([np.interp(ranks, positions, ramp[:, c]) for c in range(3)], 1)
    return rgb.reshape(noise.shape + (3,))


def shrunk(rgb):
    # half size; the tile is resized as part of a 3 x 3 tiling, so its edges stay seamless
    tiled = Image.fromarray(np.tile(rgb, (3, 3, 1)).astype(np.uint8))
    small = tiled.resize((3 * SMALL, 3 * SMALL), Image.LANCZOS)
    return small.crop((SMALL, SMALL, 2 * SMALL, 2 * SMALL))


def save_jpeg(image, path):
    image.save(path, quality=86)
    print(path.relative_to(ROOT))


def make_textures():
    ramps = json.loads((TOOLS / 'ramps.json').read_text())
    out = ASSETS / 'textures'
    out.mkdir(parents=True, exist_ok=True)
    frame, text = frame_noise(), text_noise()
    for kind in TYPES + ['dark-synchro']:
        rgb = np.clip(colored(frame, ramps[kind]['frame']), 0, 255).astype(np.uint8)
        save_jpeg(Image.fromarray(rgb), out / f'frame-{kind}.jpg')
        save_jpeg(shrunk(rgb), out / f'frame-{kind}-256.jpg')
        rgb = np.clip(colored(text, ramps[kind]['text']), 0, 255).astype(np.uint8)
        save_jpeg(shrunk(rgb), out / f'text-{kind}-256.jpg')


# ---------- ramps ----------

def ramp(pixels, n=256):
    # (without the brightest and the darkest 0.5%: the sparkles of the Xyz frame, for example)
    pixels = pixels[np.argsort(pixels.mean(1))]
    return [[round(float(v), 1) for v in pixels[int(q * (len(pixels) - 1))]] for q in np.linspace(0.005, 0.995, n)]


def make_ramps(templates):
    path = TOOLS / 'ramps.json'
    ramps = json.loads(path.read_text()) if path.exists() else {}
    for kind in TYPES:
        a = np.asarray(Image.open(Path(templates) / f'card-{kind}.png').convert('RGB')).astype(float)
        frame = np.concatenate([a[r].reshape(-1, 3) for r in FRAME_REGIONS])
        ramps[kind] = dict(frame=ramp(frame), text=ramp(a[TEXT_REGION].reshape(-1, 3)))
    path.write_text(json.dumps(ramps, separators=(',', ':')))
    print(path.relative_to(ROOT))


# ---------- the text box frame ----------

def make_frame(templates):
    # The frame is equal on the Effect, Spell, Ritual and Trap templates, the frame around it
    # and the text box inside differ: equal pixels are the frame. Its shadows (on the card
    # frame outside, on the text box inside) are made transparent black.
    kinds = ['effect', 'spell', 'ritual', 'trap']
    region = (slice(1470, 1960), slice(50, 1346))
    cards = {k: np.asarray(Image.open(Path(templates) / f'card-{k}.png').convert('RGB')).astype(float)[region]
             for k in kinds}
    difference = np.max([np.abs(cards['effect'] - cards[k]).sum(2) for k in kinds[1:]], 0)
    band = np.clip(1 - (difference - 25) / 50, 0, 1)
    labels, _ = ndimage.label(band < 0.5)
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    outside = np.isin(labels, list(border))
    solid = band >= 0.5
    inside = ~outside & ~solid
    distance, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)

    # inside: how much darker each template's text box is than its plain text box
    near = inside & (distance <= 18)
    far = inside & (distance > 16)
    shades = []
    for k in kinds:
        brightness = cards[k].mean(2)
        plain = ndimage.gaussian_filter(brightness * far, 12) / np.maximum(ndimage.gaussian_filter(far * 1.0, 12), 1e-6)
        shades.append(np.clip(1 - brightness / np.maximum(plain, 1), 0, 1))
    shadow_in = ndimage.gaussian_filter(np.median(shades, 0) * near, 0.7)

    # outside: a smooth function of the distance to the frame, measured on the top and the
    # bottom side (short at the top and the left, longer at the bottom and the right)
    r = np.arange(0, 41, 2.0)
    top = np.array([0.52, 0.37, 0.20, 0.08, 0.02] + [0.0] * 16)
    bottom = np.array([0.70, 0.56, 0.37, 0.22, 0.11, 0.06, 0.035, 0.018, 0.008, 0.003] + [0.0] * 11)
    yy, xx = np.mgrid[0:solid.shape[0], 0:solid.shape[1]]
    dy, dx = yy - iy, xx - ix
    toward = np.clip(0.5 + 0.5 * (dy + dx) / np.maximum(np.hypot(dy, dx) * np.sqrt(2), 1e-6), 0, 1)
    shadow_out = ((1 - toward) * np.interp(distance, r, top) + toward * np.interp(distance, r, bottom)) * outside

    shadow = np.maximum(shadow_in, shadow_out)
    alpha = band + (1 - band) * shadow
    rgb = np.where(band[..., None] > 0, cards['effect'] * band[..., None] / np.maximum(alpha, 1e-6)[..., None], 0)
    ys, xs = np.where(alpha > 0.02)
    crop = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    rgba = np.dstack([np.clip(rgb, 0, 255), alpha * 255])[crop]

    # at 0.75 of the size (premultiplied, so the transparent pixels do not darken the edges)
    h, w = rgba.shape[:2]
    size = (round(w * 0.75), round(h * 0.75))
    premultiplied = np.dstack([rgba[..., :3] * rgba[..., 3:] / 255, rgba[..., 3:]])
    layers = [np.asarray(Image.fromarray(premultiplied[..., c].astype(np.float32), 'F').resize(size, Image.LANCZOS))
              for c in range(4)]
    a = np.clip(layers[3], 0, 255)
    color = [np.where(a > 0.01, np.clip(layers[c], 0, 255) * 255 / np.maximum(a, 0.01), 0) for c in range(3)]
    image = np.round(np.dstack(color + [a])).clip(0, 255).astype(np.uint8)
    image[48:-48, 48:-48] = 0      # the middle is never drawn (border-image slices of 48)
    path = ASSETS / 'text-box-frame.png'
    Image.fromarray(image, 'RGBA').save(path, optimize=True)
    solid_crop = solid[crop]
    middle_row, middle_column = solid_crop.shape[0] // 2, solid_crop.shape[1] // 2
    edges = dict(top=np.argmax(solid_crop[:, middle_column]), right=np.argmax(solid_crop[middle_row, ::-1]),
                 bottom=np.argmax(solid_crop[::-1, middle_column]), left=np.argmax(solid_crop[middle_row]))
    print(path.relative_to(ROOT), 'frame edge into the image (px at 0.75):', {k: v * 0.75 for k, v in edges.items()})


# ---------- the walls ----------

WALLS = {'wall-light': ((124, 90, 44), (190, 155, 96)), 'wall-dark': ((29, 26, 23), (80, 71, 63))}


def make_walls():
    mask = np.asarray(Image.open(TOOLS / 'wall-mask.png').convert('L')).astype(float)[..., None] / 255
    grain = np.random.default_rng(3).normal(0, 2.5, mask.shape)
    for name, (ground, glyphs) in WALLS.items():
        rgb = np.array(ground) * (1 - mask) + np.array(glyphs) * mask + grain
        save_jpeg(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), ASSETS / f'{name}.jpg')


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'textures':
        make_textures()
    elif command == 'wall':
        make_walls()
    elif command == 'frame' and len(sys.argv) == 3:
        make_frame(sys.argv[2])
    elif command == 'ramps' and len(sys.argv) == 3:
        make_ramps(sys.argv[2])
    else:
        sys.exit(__doc__)
