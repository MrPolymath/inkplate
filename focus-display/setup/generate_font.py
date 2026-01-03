#!/usr/bin/env python3
"""
Generate MicroPython GFX fonts for Inkplate from TTF files.

Usage:
    python generate_font.py <ttf_file> <size> <output_name>

Example:
    python generate_font.py /System/Library/Fonts/Helvetica.ttc 72 Helvetica_72px
"""

import sys
import freetype

def generate_font(ttf_path, size, output_name, chars=None):
    """Generate a MicroPython GFX font file from a TTF font."""

    if chars is None:
        # Default character set: ASCII printable + some extras
        chars = ''.join(chr(i) for i in range(32, 127))

    face = freetype.Face(ttf_path)
    face.set_pixel_sizes(0, size)

    glyphs = []
    bitmaps = []
    total_bits = 0

    for char in chars:
        face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
        bitmap = face.glyph.bitmap

        width = bitmap.width
        height = bitmap.rows
        xoffset = face.glyph.bitmap_left
        yoffset = size - face.glyph.bitmap_top  # Adjust for baseline
        advance = face.glyph.advance.x >> 6

        # Convert bitmap to bits
        bits = []
        for row in range(height):
            for col in range(width):
                byte_idx = col // 8
                bit_idx = 7 - (col % 8)
                if byte_idx < len(bitmap.buffer[row * bitmap.pitch:row * bitmap.pitch + bitmap.pitch]):
                    pixel = (bitmap.buffer[row * bitmap.pitch + byte_idx] >> bit_idx) & 1
                    bits.append(pixel)
                else:
                    bits.append(0)

        glyphs.append({
            'char': char,
            'width': width,
            'height': height,
            'xoffset': xoffset,
            'yoffset': yoffset,
            'advance': advance,
            'bits_offset': total_bits,
        })
        bitmaps.extend(bits)
        total_bits += len(bits)

    # Pack bits into bytes
    bitmap_bytes = []
    for i in range(0, len(bitmaps), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bitmaps):
                byte |= (bitmaps[i + j] << (7 - j))
        bitmap_bytes.append(byte)

    # Generate Python module
    output = f'''# Generated font: {output_name}
# Size: {size}px
# Characters: {len(chars)}

_font_data = bytes([
    {', '.join(f'0x{b:02x}' for b in bitmap_bytes)}
])

_glyphs = {{
'''

    for g in glyphs:
        char_repr = repr(g['char'])
        output += f"    {char_repr}: ({g['bits_offset']}, {g['width']}, {g['height']}, {g['xoffset']}, {g['yoffset']}, {g['advance']}),\n"

    output += f'''}}

_height = {size}
_baseline = {size}

def get_ch(char):
    """Get glyph data for a character."""
    if char in _glyphs:
        offset, width, height, xoff, yoff, advance = _glyphs[char]
        return (_font_data, offset, width, height, xoff, yoff, advance)
    return None

# For Inkplate compatibility
height = _height
max_width = {max(g['advance'] for g in glyphs)}

def getGlyph(char):
    return get_ch(char)
'''

    return output


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("\nAvailable system fonts:")
        print("  /System/Library/Fonts/Helvetica.ttc")
        print("  /System/Library/Fonts/HelveticaNeue.ttc")
        print("  /System/Library/Fonts/SFNSMono.ttf")
        sys.exit(1)

    ttf_path = sys.argv[1]
    size = int(sys.argv[2])
    output_name = sys.argv[3]

    print(f"Generating {output_name} at {size}px from {ttf_path}...")

    content = generate_font(ttf_path, size, output_name)

    output_file = f"../{output_name}.py"
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"Created: {output_file}")
    print(f"Upload to device with: mpremote connect /dev/cu.usbserial-110 cp {output_file} :/lib/{output_name}.py")


if __name__ == "__main__":
    main()
