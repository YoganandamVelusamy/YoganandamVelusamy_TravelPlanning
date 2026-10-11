from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


WIDTH = 1800
HEIGHT = 760
SCALE = 2
OUTPUT = Path(__file__).resolve().parents[1] / "static" / "travel_hero.png"


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    for y in range(height):
        amount = y / max(1, height - 1)
        color = tuple(round(start + (end - start) * amount) for start, end in zip(top, bottom, strict=True))
        for x in range(width):
            pixels[x, y] = color
    return image


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = WIDTH * SCALE, HEIGHT * SCALE
    image = gradient((width, height), (245, 194, 151), (235, 128, 103)).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((width * 0.58, -height * 0.4, width * 1.02, height * 0.55), fill=(255, 226, 158, 175))
    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(70 * SCALE)))
    draw = ImageDraw.Draw(image, "RGBA")

    sea_top = int(height * 0.48)
    sea = gradient((width, height - sea_top), (45, 133, 139), (17, 77, 89)).convert("RGBA")
    image.alpha_composite(sea, (0, sea_top))
    draw = ImageDraw.Draw(image, "RGBA")

    draw.polygon(
        [(0, sea_top), (0, height * 0.43), (width * 0.12, height * 0.38), (width * 0.25, height * 0.44),
         (width * 0.39, height * 0.36), (width * 0.53, height * 0.45), (width * 0.72, height * 0.39),
         (width * 0.86, height * 0.45), (width, height * 0.36), (width, sea_top)],
        fill=(71, 101, 91, 170),
    )

    draw.polygon(
        [(width * 0.66, height), (width * 0.68, height * 0.72), (width * 0.72, height * 0.55),
         (width * 0.79, height * 0.5), (width * 0.86, height * 0.37), (width, height * 0.28),
         (width, height),],
        fill=(26, 75, 61, 255),
    )
    draw.polygon(
        [(width * 0.78, height), (width * 0.81, height * 0.68), (width * 0.85, height * 0.58),
         (width * 0.91, height * 0.53), (width, height * 0.45), (width, height)],
        fill=(20, 62, 52, 255),
    )

    house_colors = [(255, 224, 186, 255), (255, 241, 212, 255), (231, 142, 108, 255),
                    (243, 193, 132, 255), (235, 220, 190, 255), (202, 112, 88, 255)]
    houses = [
        (0.70, 0.56, 0.055, 0.09), (0.75, 0.50, 0.045, 0.08), (0.80, 0.44, 0.05, 0.085),
        (0.85, 0.36, 0.045, 0.09), (0.90, 0.34, 0.055, 0.10), (0.76, 0.61, 0.04, 0.075),
        (0.83, 0.55, 0.042, 0.08), (0.91, 0.48, 0.048, 0.085), (0.96, 0.43, 0.04, 0.08),
        (0.72, 0.68, 0.04, 0.075), (0.87, 0.66, 0.05, 0.09), (0.94, 0.59, 0.045, 0.08),
    ]
    for index, (x, y, house_width, house_height) in enumerate(houses):
        left = int(width * x)
        top = int(height * y)
        right = int(width * (x + house_width))
        bottom = int(height * (y + house_height))
        draw.rectangle((left, top, right, bottom), fill=house_colors[index % len(house_colors)])
        roof_height = int((right - left) * 0.42)
        draw.polygon([(left - 3, top), ((left + right) // 2, top - roof_height), (right + 3, top)],
                     fill=(166, 77, 61, 255))
        window = max(3, int(width * 0.003))
        for window_x in (left + int((right - left) * 0.25), left + int((right - left) * 0.68)):
            draw.rectangle((window_x, top + int((bottom - top) * 0.35), window_x + window,
                            top + int((bottom - top) * 0.57)), fill=(43, 73, 67, 255))

    for row in range(9):
        y = int(height * (0.58 + row * 0.047))
        start = int(width * (0.24 + (row % 3) * 0.06))
        for col in range(7):
            x = start + col * int(width * 0.09)
            if x < width * 0.69:
                length = int(width * (0.02 + (col % 3) * 0.007))
                draw.line((x, y, x + length, y - 1), fill=(174, 221, 208, 85), width=2 * SCALE)

    for x, y, radius in ((0.16, 0.56, 0.016), (0.34, 0.66, 0.01), (0.48, 0.52, 0.012)):
        center_x, center_y = int(width * x), int(height * y)
        draw.ellipse((center_x - radius * width, center_y - radius * height,
                      center_x + radius * width, center_y + radius * height), fill=(255, 244, 218, 210))

    image = image.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    image.save(OUTPUT, optimize=True)


if __name__ == "__main__":
    main()