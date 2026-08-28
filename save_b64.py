import json, sys, base64, os

# Read base64 chunks from stdin lines (each line is a chunk)
chunks = []
for line in sys.stdin:
    line = line.strip()
    if line:
        chunks.append(line)

b64_all = ''.join(chunks)
img_data = base64.b64decode(b64_all)
path = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi\browser_cap.png'
with open(path, 'wb') as f:
    f.write(img_data)
print(f'Saved: {len(img_data)} bytes to {path}')
