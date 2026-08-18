"""Create a minimal valid ICO file for Tauri."""
import struct
import io

# ICO file format: https://en.wikipedia.org/wiki/ICO_(file_format)
# Header: 6 bytes (reserved, type, count)
# Directory entry: 16 bytes per image
# Image data: BMP format (NOT PNG) for ICO

width = 16
height = 16
bpp = 32  # bits per pixel

# Create BMP data (BITMAPINFOHEADER + pixel data + AND mask)
bmp_header = struct.pack('<IiiHHIIiiII',
    40,           # header size
    width,        # width
    height * 2,   # height (doubled for ICO format)
    1,            # planes
    bpp,          # bits per pixel
    0,            # compression (BI_RGB)
    0,            # image size (can be 0 for BI_RGB)
    0,            # x pixels per meter
    0,            # y pixels per meter
    0,            # colors in palette
    0             # important colors
)

# Pixel data (BGRA, bottom-up)
pixel_data = b''
for y in range(height):
    for x in range(width):
        # Green pixel with alpha
        pixel_data += bytes([0, 255, 0, 255])

# AND mask (all zeros = fully opaque)
and_mask = bytes(((width + 31) // 32) * 4 * height)

image_data = bmp_header + pixel_data + and_mask
image_size = len(image_data)

# ICO header
ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved, type=ICO, count=1

# Directory entry
dir_entry = struct.pack('<BBBBHHII',
    width if width < 256 else 0,   # width
    height if height < 256 else 0, # height
    0,            # colors in palette
    0,            # reserved
    1,            # color planes
    bpp,          # bits per pixel
    image_size,   # size of image data
    6 + 16        # offset to image data (header + 1 dir entry)
)

# Write ICO file
with open('src-tauri/icons/icon.ico', 'wb') as f:
    f.write(ico_header)
    f.write(dir_entry)
    f.write(image_data)

print(f'Created ICO: {6 + 16 + image_size} bytes')
