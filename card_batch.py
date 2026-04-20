"""
Read a card list file and produce a multi-page print-ready PDF.

The card list is a text file where each line specifies an image path
and the number of copies to include, separated by whitespace:

    cards/fireball.png 4
    cards/heal.png 2
    cards/shield.png 3

This expands into a flat list (4x fireball, 2x heal, 3x shield = 9 cards)
which gets split across pages of 9 cards each.

Blank lines and lines starting with # are ignored.
"""

import argparse
import sys
from pathlib import Path

from card_sheet import build_multipage_pdf


def parse_card_list(list_path):
    """
    Parse a card list file into a flat list of image paths,
    with each path repeated according to its copy count.
    """
    expanded = []
    list_dir = list_path.parent

    with open(list_path) as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.rsplit(maxsplit=1)
            if len(parts) != 2:
                sys.exit(
                    f"Error on line {line_num}: expected '<image_path> <count>', "
                    f"got: {line!r}"
                )

            image_str, count_str = parts

            try:
                count = int(count_str)
            except ValueError:
                sys.exit(
                    f"Error on line {line_num}: count must be an integer, "
                    f"got: {count_str!r}"
                )

            if count < 1:
                sys.exit(f"Error on line {line_num}: count must be at least 1")

            # Resolve relative paths against the list file's directory
            image_path = Path(image_str)
            if not image_path.is_absolute():
                image_path = list_dir / image_path

            if not image_path.is_file():
                sys.exit(f"Error on line {line_num}: file not found: {image_path}")

            expanded.extend([image_path] * count)

    return expanded


def main():
    parser = argparse.ArgumentParser(
        description="Generate print sheets from a card list file."
    )
    parser.add_argument(
        "card_list",
        help="Text file with '<image_path> <count>' per line",
    )
    parser.add_argument(
        "-o", "--output",
        default="card_sheets.pdf",
        help="Output PDF filename (default: card_sheets.pdf)",
    )

    args = parser.parse_args()
    list_path = Path(args.card_list)

    if not list_path.is_file():
        sys.exit(f"Error: card list not found: {list_path}")

    all_cards = parse_card_list(list_path)

    if not all_cards:
        sys.exit("Error: card list is empty")

    print(f"Expanded {list_path.name} to {len(all_cards)} total card(s)")
    build_multipage_pdf(all_cards, Path(args.output))


if __name__ == "__main__":
    main()
