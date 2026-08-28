import requests, re
requests.packages.urllib3.disable_warnings()
s = requests.Session(); s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})
r = s.get('https://www.qianlima.com/hot1700955/', timeout=15)
html = r.text

m = re.search(r'STATIC_DATA_\s*=\s*function\s*\(\)\s*\{\s*return\s*(.*?);\s*\}\s*</script>', html, re.DOTALL)
block = m.group(1)

# Find ALL positions of 'content:' in the block
positions = []
pos = 0
while True:
    pos = block.find('content:', pos)
    if pos < 0:
        break
    # Check if it's preceded by a word boundary (not part of contentid/contentId)
    if pos > 0 and block[pos-1].isalnum():
        pos += 1
        continue
    positions.append(pos)
    pos += 1

print(f'Found {len(positions)} "content:" occurrences')
for i, p in enumerate(positions[:5]):
    print(f'\n--- Occurrence {i} at pos {p} ---')
    snippet = block[max(0,p-20):p+80]
    print(f'  Context: ...{snippet}...')

# Also find all "contentid:" positions
cid_positions = []
pos = 0
while True:
    pos = block.find('contentid:', pos)
    if pos < 0:
        break
    cid_positions.append(pos)
    pos += 1
print(f'\nFound {len(cid_positions)} "contentid:" occurrences')

# Check different content-containing sections
# Look for patterns like: someList: [{contentid:..., content:"..."}]
content_sections = re.findall(r'(\w+):\s*\[[^\]]*?content:', block)
print(f'Sections with content keyword: {content_sections}')

# Check for "budget" in block
if '预算' in block:
    # Find context
    all_budget = re.findall(r'.{0,30}预算.{0,60}', block)
    for i, ctx in enumerate(all_budget[:5]):
        print(f'\nBudget context {i}: {ctx[:100]}')
