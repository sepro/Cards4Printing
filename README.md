# Card Sheet Printer

Generate print-ready PDF sheets from high-resolution card game images. Cards are laid out on A4 portrait pages with trim marks for precise cutting to exactly 63mm × 88mm (standard poker size).

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Input images

Each card image should be **3288 × 4488 pixels at 1200 DPI**. This includes a bleed area of roughly 3.3mm on each side beyond the 63 × 88mm trim line. The bleed ensures no white edges appear if your cuts are slightly off.

PNG and JPG are both supported.

## Usage

### Single sheet (up to 9 cards)

Pass image files directly on the command line:

```
python card_sheet.py card1.png card2.png card3.png -o output/sheet.pdf
```

If you omit `-o`, the output defaults to `card_sheet.pdf`.

### Batch mode (any number of cards, multiple copies)

Create a text file listing each card image and the number of copies you need:

```
# my_deck.txt
images/fireball.png 4
images/heal.png 2
images/shield.png 1
```

Then run:

```
python card_batch.py examples/my_deck.txt -o output/my_deck.pdf
```

Cards are expanded (4× fireball = 4 slots) and packed 9 per page across as many pages as needed. Blank lines and lines starting with `#` are ignored. Image paths are resolved relative to the text file's location.

Both scripts must be in the same directory since `card_batch.py` imports from `card_sheet.py`.

## Printer settings

Getting the correct physical size depends entirely on your printer not scaling the PDF. These settings matter:

- **Paper size:** A4
- **Orientation:** Portrait
- **Scaling: "Actual size" or 100%** — this is the most important setting. Use this setting first, then check how large the resulting cards are, they should be exactly 63x88mm. If not calculate the % required. On my printer, with borderless printing enabled on photo paper, this turned out to be 98.7%. 
- **Margins:** Your printer's minimum margins should be fine. The layout leaves roughly 4mm on the sides and 6mm on top and bottom, which is within the printable area of most inkjet and laser printers.
- **Quality:** Use the highest quality setting your printer offers, especially for inkjet. The source images are 1200 DPI, so a high print resolution will preserve detail.
- **Paper type:** For best results, use a heavier stock (200–300 gsm cardstock). Set the paper type in your printer driver to match — this affects ink coverage and drying time.

### Verifying the output

Before printing an entire deck, print a single test page and measure a card with a ruler. The trim marks should be exactly 63mm apart horizontally and 88mm apart vertically. If the measurements are off, your printer is applying some scaling — check the settings above.

### Cutting tips

Each card has L-shaped trim marks at all four corners. Between adjacent cards, a single shared tick mark sits in the gap. Use a metal ruler and a sharp craft knife or rotary cutter for clean edges. A cutting mat is strongly recommended.

## Layout details

- **Grid:** 3 columns × 3 rows per page (9 cards)
- **Card trim size:** 63mm × 88mm
- **Image size with bleed:** ~69.6mm × 95.0mm
- **Bleed overlap:** adjacent columns overlap by ~3.3mm of bleed so the grid fits A4 portrait with usable margins. Trim areas never overlap — only bleed, which is cut away.
- **Page margins:** ~3.9mm left/right, ~6mm top/bottom
- **Trim marks:** Medium gray (50%) so they're visible against both white paper and dark bleed areas. Exterior corners get L-shaped ticks; adjacent cards share a single tick centered in the gap.
