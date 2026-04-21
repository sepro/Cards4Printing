"""
Compose up to 9 card game images onto a printable A4 portrait PDF
with per-card trim marks for precise cutting.

Card dimensions: 63mm x 88mm (standard poker size)
Input images: 3288x4488 pixels at 1200 DPI (includes bleed area)
Output: A4 portrait PDF with 3x3 grid.

Three full card images side-by-side (3 * 69.60 = 208.80mm) would leave
only 0.6mm of margin on an A4 page, which most printers cannot reach.
Adjacent bleed regions are therefore overlapped horizontally by up to
one bleed width so the grid fits with a usable margin. Trim (card)
areas never overlap — only bleed, which is discarded at cutting.
"""

import argparse
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# --- Card and image geometry ---

CARD_WIDTH_MM = 63.0
CARD_HEIGHT_MM = 88.0

IMAGE_PIXELS_W = 3288
IMAGE_PIXELS_H = 4488
IMAGE_DPI = 1200

# Full image dimensions in mm (card + bleed on all sides)
IMAGE_WIDTH_MM = (IMAGE_PIXELS_W / IMAGE_DPI) * 25.4  # ~69.60mm
IMAGE_HEIGHT_MM = (IMAGE_PIXELS_H / IMAGE_DPI) * 25.4  # ~95.00mm

BLEED_X = (IMAGE_WIDTH_MM - CARD_WIDTH_MM) / 2  # ~3.30mm
BLEED_Y = (IMAGE_HEIGHT_MM - CARD_HEIGHT_MM) / 2  # ~3.50mm

GRID_COLS = 3
GRID_ROWS = 3

# Horizontal bleed overlap between adjacent columns, in mm. Kept <= BLEED_X
# so card trim areas never overlap — only bleed, which is cut away.
# Default: full bleed overlap so the grid fits A4 portrait with margin.
OVERLAP_X_MM = BLEED_X
OVERLAP_Y_MM = 0.0

# Trim mark appearance
MARK_LENGTH = 3.0 * mm
MARK_GAP = 0.5 * mm     # gap between image edge and start of mark
MARK_THICKNESS = 0.3     # line width in points


def cell_pitch():
    """Centre-to-centre spacing between adjacent cells, in points."""
    pitch_x = (IMAGE_WIDTH_MM - OVERLAP_X_MM) * mm
    pitch_y = (IMAGE_HEIGHT_MM - OVERLAP_Y_MM) * mm
    return pitch_x, pitch_y


def compute_layout(page_w, page_h):
    """
    Calculate the origin so that the 3x3 grid of full images
    (including bleed, minus any configured overlap) is centered
    on the portrait page.

    Returns the bottom-left corner of the grid in page coordinates.
    """
    pitch_x, pitch_y = cell_pitch()
    grid_w = (GRID_COLS - 1) * pitch_x + IMAGE_WIDTH_MM * mm
    grid_h = (GRID_ROWS - 1) * pitch_y + IMAGE_HEIGHT_MM * mm

    origin_x = (page_w - grid_w) / 2
    origin_y = (page_h - grid_h) / 2

    return origin_x, origin_y


def draw_all_trim_marks(c, origin_x, origin_y, occupied_cells):
    """
    Draw trim ticks for all occupied cards.

    There are two kinds of tick:
    - Exterior: on the page-margin side of an edge card. Drawn with a gap
      from the bleed edge, extending outward into the margin.
    - Interior (shared): between two adjacent cards. A single short tick
      centered in the gap between the two bleed areas, respecting the
      gap distance from both images.

    Horizontal trim lines (top/bottom of each card) need vertical ticks.
    Vertical trim lines (left/right of each card) need horizontal ticks.
    """
    pitch_x, pitch_y = cell_pitch()
    card_w = CARD_WIDTH_MM * mm
    card_h = CARD_HEIGHT_MM * mm
    bx = BLEED_X * mm
    by = BLEED_Y * mm
    ox = OVERLAP_X_MM * mm
    oy = OVERLAP_Y_MM * mm
    gap = MARK_GAP
    exterior_length = MARK_LENGTH

    # Interior tick: spans the gap between two adjacent cards' trim edges.
    # Without overlap that's 2*bleed; overlap eats into the bleed gap.
    # Shortened 1mm on each end so slight cutting offsets don't leave the
    # tick visible on the finished card.
    interior_inset = 1.0 * mm
    interior_h_tick = max(2 * bx - ox - 2 * gap - 2 * interior_inset, 0.5 * mm)
    interior_v_tick = max(2 * by - oy - 2 * gap - 2 * interior_inset, 0.5 * mm)

    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(MARK_THICKNESS)

    # Track which ticks we've drawn to avoid duplicates at shared edges
    drawn_ticks = set()

    for col, row in occupied_cells:
        img_x = origin_x + col * pitch_x
        img_y = origin_y + row * pitch_y
        trim_x = img_x + bx
        trim_y = img_y + by

        # Each card edge can have ticks at both ends (the two corners).
        # For each corner we need a horizontal tick and a vertical tick.
        for corner_col, corner_row in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            # The trim corner position
            cx = trim_x + corner_col * card_w
            cy = trim_y + corner_row * card_h

            # --- Horizontal tick (marks a vertical trim line) ---
            # Direction points away from the card center
            dx = -1 if corner_col == 0 else +1
            h_neighbor_col = col + dx
            has_h_neighbor = (h_neighbor_col, row) in occupied_cells

            # Unique key: the vertical trim line x + the y position
            h_tick_key = (round(cx, 2), round(cy, 2), "h")
            if h_tick_key not in drawn_ticks:
                drawn_ticks.add(h_tick_key)

                if has_h_neighbor:
                    # Shared tick centered in the gap between the two trim edges
                    mid_x = cx + dx * (bx - ox / 2)
                    half = interior_h_tick / 2
                    c.line(mid_x - half, cy, mid_x + half, cy)
                else:
                    # Exterior tick moved inside the bleed so it isn't
                    # clipped by the printer's unprintable page margin.
                    h_start = cx + dx * gap
                    h_length = min(exterior_length, bx - gap)
                    h_end = h_start + dx * h_length
                    c.line(h_start, cy, h_end, cy)

            # --- Vertical tick (marks a horizontal trim line) ---
            dy = -1 if corner_row == 0 else +1
            v_neighbor_row = row + dy
            has_v_neighbor = (col, v_neighbor_row) in occupied_cells

            v_tick_key = (round(cx, 2), round(cy, 2), "v")
            if v_tick_key not in drawn_ticks:
                drawn_ticks.add(v_tick_key)

                if has_v_neighbor:
                    mid_y = cy + dy * (by - oy / 2)
                    half = interior_v_tick / 2
                    c.line(cx, mid_y - half, cx, mid_y + half)
                else:
                    # Top/bottom ticks moved inside the bleed so they
                    # aren't clipped by the printer's unprintable margin.
                    v_start = cy + dy * gap
                    v_length = min(exterior_length, by - gap)
                    v_end = v_start + dy * v_length
                    c.line(cx, v_start, cx, v_end)


def place_card_image(c, image_path, origin_x, origin_y, col, row, occupied_cells):
    """
    Place one card image in its grid cell, clipped so that any overlap
    with a neighbouring card is split 50/50 along the middle of the
    overlap zone (instead of one card fully overwriting the other).
    """
    pitch_x, pitch_y = cell_pitch()
    img_w = IMAGE_WIDTH_MM * mm
    img_h = IMAGE_HEIGHT_MM * mm
    ox = OVERLAP_X_MM * mm
    oy = OVERLAP_Y_MM * mm

    img_x = origin_x + col * pitch_x
    img_y = origin_y + row * pitch_y

    # Shrink the draw window by half the overlap on each side that has a
    # neighbour, so the other half of that overlap belongs to the neighbour.
    clip_x0 = img_x + (ox / 2 if (col - 1, row) in occupied_cells else 0)
    clip_x1 = img_x + img_w - (ox / 2 if (col + 1, row) in occupied_cells else 0)
    clip_y0 = img_y + (oy / 2 if (col, row - 1) in occupied_cells else 0)
    clip_y1 = img_y + img_h - (oy / 2 if (col, row + 1) in occupied_cells else 0)

    c.saveState()
    p = c.beginPath()
    p.rect(clip_x0, clip_y0, clip_x1 - clip_x0, clip_y1 - clip_y0)
    c.clipPath(p, stroke=0, fill=0)

    c.drawImage(
        str(image_path),
        img_x, img_y,
        width=img_w, height=img_h,
        preserveAspectRatio=True,
    )
    c.restoreState()


def build_page(c, image_paths, page_w, page_h):
    """Compose up to 9 card images onto the current PDF page."""
    max_cards = GRID_COLS * GRID_ROWS
    image_paths = image_paths[:max_cards]

    origin_x, origin_y = compute_layout(page_w, page_h)

    card_positions = []
    for idx, img in enumerate(image_paths):
        col = idx % GRID_COLS
        row = (GRID_ROWS - 1) - (idx // GRID_COLS)
        card_positions.append((img, col, row))

    occupied_cells = set((col, row) for _, col, row in card_positions)

    for img, col, row in card_positions:
        place_card_image(c, img, origin_x, origin_y, col, row, occupied_cells)

    draw_all_trim_marks(c, origin_x, origin_y, occupied_cells)

    return len(image_paths)


def build_multipage_pdf(all_image_paths, output_path):
    """
    Split a list of card images across multiple pages (8 per page)
    and save as a single PDF (9 per page).
    """
    cards_per_page = GRID_COLS * GRID_ROWS
    page_size = A4
    page_w, page_h = page_size

    c = canvas.Canvas(str(output_path), pagesize=page_size)

    total_pages = (len(all_image_paths) + cards_per_page - 1) // cards_per_page
    for page_idx in range(total_pages):
        start = page_idx * cards_per_page
        page_images = all_image_paths[start : start + cards_per_page]

        if page_idx > 0:
            c.showPage()

        count = build_page(c, page_images, page_w, page_h)
        print(f"  Page {page_idx + 1}: {count} card(s)")

    c.save()
    print(f"Saved {total_pages} page(s) to {output_path}")


def build_sheet(image_paths, output_path):
    """Compose images onto A4 landscape page(s) and save as PDF."""
    if not image_paths:
        sys.exit("Error: no images provided.")

    build_multipage_pdf(image_paths, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Arrange card images on an A4 portrait sheet with cutting guides."
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="1-9 card image files (png or jpg, 3288x4488 @ 1200 DPI)",
    )
    parser.add_argument(
        "-o", "--output",
        default="card_sheet.pdf",
        help="Output PDF filename (default: card_sheet.pdf)",
    )

    args = parser.parse_args()

    for img in args.images:
        if not Path(img).is_file():
            sys.exit(f"Error: file not found: {img}")

    build_sheet([Path(p) for p in args.images], Path(args.output))


if __name__ == "__main__":
    main()
