"""
Complete hljcg scraper using browser + OCR approach.
Strategy: 
1. Open browser page
2. Click region "鸡西市"
3. Refresh captcha, extract base64, recognize
4. Fill captcha, click search
5. Extract table data, paginate through all pages
6. Save to JSON
"""
import json, sys, os, time, subprocess, re, base64, urllib.request, urllib.parse, gzip, http.cookiejar

# Paths
NODE = None
for d in sorted([d for d in os.listdir(r'C:\Program Files\QClaw') if d.startswith('v')], reverse=True):
    n = rf'C:\Program Files\QClaw\{d}\resources\node\node.exe'
    if os.path.exists(n):
        NODE = n
        break

XB = os.path.expanduser(r'~/.qclaw/skills/xbrowser/scripts/xb.cjs')
WORKDIR = r'C:\Users\Admin\.qclaw\workspace\ccgp_jixi'

def xb_eval(js_code):
    """Run eval in browser and return result string"""
    cmd = [NODE, XB, 'run', '--browser', 'edge', 'eval', js_code]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=WORKDIR)
        data = json.loads(r.stdout)
        if data.get('ok'):
            return data['data']['result']['data']['result']
        else:
            print(f"xb eval error: {data.get('error', 'unknown')}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"xb eval exception: {e}", file=sys.stderr)
        return None

# Step 1: Refresh captcha and get base64
js = """
var imgs = document.querySelectorAll('img');
var cap = null;
for (var i = 0; i < imgs.length; i++) {
    if (imgs[i].src.indexOf('getVerify') > -1) {
        cap = imgs[i];
        break;
    }
}
if (cap) {
    var c = document.createElement('canvas');
    c.width = cap.width;
    c.height = cap.height;
    var ctx = c.getContext('2d');
    ctx.drawImage(cap, 0, 0);
    window.__hljcg_captcha = c.toDataURL('image/png');
    'ok:' + window.__hljcg_captcha.length;
} else {
    'no captcha img';
}
"""
result = xb_eval(js)
print(f"Captcha: {result[:100] if result else 'None'}")

if result and result.startswith('ok:'):
    # Extract base64 data
    b64 = xb_eval("window.__hljcg_captcha")
    if b64 and b64.startswith('data:image'):
        # Save
        img_data = base64.b64decode(b64.split(',')[1])
        path = os.path.join(WORKDIR, 'hljcg_captcha.png')
        with open(path, 'wb') as f:
            f.write(img_data)
        print(f"Saved captcha: {len(img_data)} bytes to {path}")
    else:
        print(f"Captcha data: {b64[:100] if b64 else 'None'}")
