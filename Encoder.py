from PIL import Image
from tkinter import Tk, filedialog
import math
import os

# =========================
# SETTINGS
# =========================

WIDTH = int(input("Input image Width: "))
HEIGHT = int(input("Input image Height: "))

BLOCK_SIZE = 512   # Keep this the same unless you know what you're doing
SECTION_BLOCKS = int(input("Enter Section Blocks (140 Works the best, lower the number for lower end computers): "))
OUTPUT_FILE = "image data.txt"
PALETTE_FILE = "imagehex.txt"

SYMBOLS = list(
    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃ"
)

COLOR_COUNT = int(input("Enter Color Count: "))

# =========================

def selectimage():
    root = Tk()
    root.withdraw()

    return filedialog.askopenfilename(
        title="Select Image",
        filetypes=[
            ("PNG Images", "*.png")
        ]
    )


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def generate_palette(img, Method):

    if Method == 1:
        method = Image.Quantize.MEDIANCUT

    elif Method == 2:
        method = Image.Quantize.MAXCOVERAGE

    elif Method == 3:
        method = Image.Quantize.FASTOCTREE

    else:
        print("Invalid choice, using Median Cut.")
        method = Image.Quantize.MEDIANCUT

    quantized = img.convert("RGB").quantize(
        colors=COLOR_COUNT,
        method=method
    )

    palette = quantized.getpalette()
    colors = quantized.getcolors()

    colors.sort(reverse=True)

    final_palette = []

    for count, index in colors:
        r = palette[index * 3]
        g = palette[index * 3 + 1]
        b = palette[index * 3 + 2]

        final_palette.append((r, g, b))

    return final_palette

def get_closest_symbol(pixel, palette, symbols):

    r, g, b = pixel

    best_symbol = None
    best_distance = float("inf")

    for symbol, (pr, pg, pb) in zip(symbols, palette):

        distance = (
            (r - pr) ** 2 +
            (g - pg) ** 2 +
            (b - pb) ** 2
        )

        if distance < best_distance:
            best_distance = distance
            best_symbol = symbol

    return best_symbol

def save(palette):

    with open(PALETTE_FILE, "w", encoding="utf-8") as f:

        for color in palette:
            f.write(rgb_to_hex(color) + "\n")

def encode_image(img, palette):

    encoded = []

    for x in range(WIDTH):
        for y in range(HEIGHT):

            pixel = img.getpixel((x, y))

        symbol = get_closest_symbol(
        pixel,
        palette,
        SYMBOLS
    )

    encoded.append(symbol)

    return "".join(encoded)

def rle_encode(data):

    if not data:
        return ""

    result = []

    current = data[0]
    count = 0

    for char in data[1:]:

        if char == current:
            count += 1
        else:
            result.append(f"{current}{count}:")
            current = char
            count = 0

    result.append(f"{current}{count}:")

    return "".join(result)

def save_encoded(data):

    # Build lines first
    lines = []
    current_line = ""

    entries = data.split(":")

    for entry in entries:

        if not entry:
            continue

        token = entry + ":"

        if len(current_line) + len(token) > BLOCK_SIZE:

            lines.append(current_line)
            current_line = token

        else:
            current_line += token

    if current_line:
        lines.append(current_line)

    # Split lines into files
    file_number = 0

    for start in range(0, len(lines), SECTION_BLOCKS):

        filename = f"image{file_number:02d}.txt"

        with open(filename, "w", encoding="utf-8") as f:

            chunk = lines[start:start + SECTION_BLOCKS]

            for line in chunk:
                f.write(line + "\n")

            # blank final line
            f.write("\n")

        print(f"Saved {filename}")

        file_number += 1

def create_preview(img, palette):

    preview = Image.new("RGB", (WIDTH, HEIGHT))

    for x in range(WIDTH):
        for y in range(HEIGHT):

            pixel = img.getpixel((x, y))

            best_color = None
            best_distance = float("inf")

            r, g, b = pixel[:3]

            for pr, pg, pb in palette:

                distance = (
                    (r - pr) ** 2 +
                    (g - pg) ** 2 +
                    (b - pb) ** 2
                )

                if distance < best_distance:
                    best_distance = distance
                    best_color = (pr, pg, pb)

            preview.putpixel((x, y), best_color)

    preview.save("preview.png")

    return preview

def main():

    imagepath = selectimage()

    if not imagepath:
        print("No file selected.")
        return

    print("Loading image...")

    img = Image.open(imagepath)
    img = img.convert("RGB")
    img = img.resize((WIDTH, HEIGHT))

    print(f"Generating {COLOR_COUNT} colors...")

    print("\nPalette Generation Method:")
    print("1 - Median Cut (Default)")
    print("2 - Max Coverage")
    print("3 - Fast Octree (best-ish)")

    Method = int(input("Choose method (1-3): "))

    palette = generate_palette(img, Method)

    print("Generating preview...")
    create_preview(img, palette)

    print("Saving palette...")
    save(palette)

    print("Encoding image...")

    encoded = encode_image(img, palette)

    print("Compressing...")
    encoded = rle_encode(encoded)

    print("Saving image data...")
    save_encoded(encoded)

    print()
    print("Done!")
    print(f"Palette: {PALETTE_FILE}")
    print(f"Encoded image: {OUTPUT_FILE}")
    print(f"Colors used: {len(palette)}")
    print(f"Characters encoded: {len(encoded):,}")

    os.startfile("preview.png")

if __name__ == "__main__":
    main()
