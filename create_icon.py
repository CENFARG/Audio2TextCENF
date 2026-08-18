import zlib, struct

w = 16
h = 16
raw = bytes([0, 0, 255, 0] * w * h)

def chunk(ctype, data):
    c = ctype + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

with open('src-tauri/icons/icon.png', 'wb') as f:
    f.write(png)
print('OK')
