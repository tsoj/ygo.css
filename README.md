# ygo.css

A stylesheet in the materials of Yu-Gi-Oh! cards: card frames, name boxes, text boxes and
attributes, with hard bevels as in Windows 98. Like [98.css](https://jdan.github.io/98.css/),
it styles some elements by themselves and gives classes for the rest. `index.html` shows all of
it.

## Use

```html
<head>
    <script src="ygo.css/ygo.js"></script>   <!-- the theme, before the first paint -->
    <link rel="stylesheet" href="ygo.css/ygo.css">
</head>
```

The stylesheet finds its images and fonts in `assets/`, next to it.

## Card types

`data-card` on any element sets its card type: `normal`, `effect`, `ritual`, `fusion`,
`synchro`, `xyz`, `link`, `spell`, `trap`, `dark-synchro`. The elements inside take it on.
Without one: Normal, in the dark theme Dark Synchro.

## Components

| Class or element | What it is |
|---|---|
| `body` | A wall of hieroglyphs |
| `.card-frame` | A panel of card frame, with raised edges |
| `.name-box` | A raised box with a card name |
| `.attribute` | An attribute icon: DARK, or LIGHT with `data-attribute="light"` |
| `.text-box` | The framed text box of a card; `.type-line` inside: `[Spellcaster/Effect]`. A `table.text-box` gets ruled rows |
| `.stat-box` | A small box of a card type: a ring of its frame around its text box |
| `.art-box` | The steel frame around a card's art, dark inside (for code, output) |
| `button`, `.button`, `input[type=submit]` | Raised boxes in the card type's frame; pressed in when clicked |
| `input`, `select`, `textarea` | Sunken text box fields |
| `hr` | An etched line |

## Light and dark theme

The theme is light (Normal monster) unless dark (Dark Synchro) was chosen: `data-theme="dark"`
on `<html>`. `ygo.js` sets it before the first paint from the stored choice (localStorage
`ygo-theme`) and switches it when an element with the class `ygo-theme-toggle` is clicked. The
switch can be an attribute, which shows the attribute of the theme it switches to:

```html
<button class="attribute ygo-theme-toggle" type="button" aria-label="Light / dark theme"></button>
```

## Variables

Other stylesheets can use the variables of ygo.css: `--card-frame`, `--card-frame-small`,
`--card-text` (textures), `--card-hi`, `--card-lo`, `--card-ink` (colors of the card type),
`--ygo-raised`, `--ygo-sunken` (border colors of the bevels), `--ygo-text-box-frame`,
`--ygo-font-name`, `--ygo-font-text`, `--ygo-font-type`, `--ygo-ink`, `--ygo-link`.

A texture is drawn at its own size: `--card-frame` as a 512px tile, `--card-frame-small` and
`--card-text` as 256px tiles. A tile scaled by the browser can show its edges as thin lines.

## Assets

`tools/make_assets.py` makes the textures, the text box frame and the walls (see its
description). The textures are periodic noise in the colors of the card templates of
[kooriookami/yugioh-card](https://github.com/kooriookami/yugioh-card); the text box frame is cut
from those templates. The fonts and the attribute icons are from that project too. The wall is
made from the Papyrus of Ani
([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Papyrus_ani_curs_hiero.jpg),
public domain), with a glyph made from a Black Rose Dragon picture.

## License

The code (CSS, JavaScript, tools) is MIT licensed. The card designs, the fonts and the card art
belong to their owners (Konami, the fonts' foundries, the artists): this is a fan work.
