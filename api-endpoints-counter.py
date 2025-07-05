#!/usr/bin/env python3
# API Endpoints Counter by Sid github.com/dr34mhacks

import argparse
import json
import re
from collections import Counter, deque
from urllib.parse import urlparse

import yaml  # pip install pyyaml

def flatten_postman_items(items):
    queue = deque(items)
    while queue:
        it = queue.popleft()
        if not isinstance(it, dict):
            continue
        if 'request' in it:
            yield it
        if 'item' in it and isinstance(it['item'], list):
            queue.extend(it['item'])

def extract_postman_path(raw_url):
    if isinstance(raw_url, dict):
        if isinstance(raw_url.get('path'), list):
            segments = raw_url['path']
        else:
            segments = [seg for seg in urlparse(raw_url.get('raw', '')).path.split('/') if seg]
    else:
        segments = [seg for seg in urlparse(raw_url or '').path.split('/') if seg]

    norm = []
    for seg in segments:
        seg = seg.split('?', 1)[0].split('#', 1)[0].rstrip('/')
        m = re.match(r'\{\{\s*(\w+)\s*\}\}', seg)
        norm.append(f":{m.group(1)}") if m else norm.append(seg)
    return '/' + '/'.join(norm) if norm else '/'

def parse_postman(data):
    total = 0
    methods = Counter()
    endpoints = Counter()
    bases = Counter()

    for item in flatten_postman_items(data.get('item', [])):
        req = item.get('request', {})
        raw_url = req.get('url')
        if not raw_url:
            continue

        method = req.get('method', 'UNKNOWN').upper()
        path = extract_postman_path(raw_url)

        total += 1
        methods[method] += 1
        endpoints[path] += 1

        parts = [s for s in path.split('/') if s]
        if parts and re.match(r'^v\d+$', parts[0], re.IGNORECASE):
            base = parts[1] if len(parts) > 1 else parts[0]
        else:
            base = parts[0] if parts else '(root)'
        bases[base] += 1

    return total, methods, endpoints, bases

def parse_swagger(data):
    total = 0
    methods = Counter()
    endpoints = Counter()
    bases = Counter()

    for raw_path, ops in data.get('paths', {}).items():
        norm_path = re.sub(r'\{(\w+)\}', r':\1', raw_path.rstrip('/'))
        if not norm_path.startswith('/'):
            norm_path = '/' + norm_path

        parts = [p for p in norm_path.split('/') if p]
        if parts and re.match(r'^v\d+$', parts[0], re.IGNORECASE):
            base = parts[1] if len(parts) > 1 else parts[0]
        else:
            base = parts[0] if parts else '(root)'

        for method in ops:
            if method.lower() in {'get','post','put','patch','delete','options','head','trace'}:
                total += 1
                m = method.upper()
                methods[m] += 1
                endpoints[norm_path] += 1
                bases[base] += 1

    return total, methods, endpoints, bases

def generate_html(total, methods, endpoints, bases):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>API Endpoints Counter</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body {{ margin:0; padding:0; background:#f0f2f5; font-family:'Roboto',sans-serif; }}
    .container {{ max-width:960px; margin:2rem auto; background:#fff; padding:2rem; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
    h1 {{ text-align:center; margin-bottom:1rem; color:#324551; /* primary */ }}
    h2 {{ margin-top:2rem; color:#4a4a4a; }}
    table {{ width:100%; border-collapse:collapse; margin-top:1rem; }}
    th, td {{ padding:.75rem 1rem; text-align:left; }}
    th {{ background:#324551; /* accent */ color:#fff; }}
    tr:nth-child(even) {{ background:#f9f9f9; }}
    tr:hover {{ background:rgba(219,37,64,0.1); /* subtle accent hover */ }}
    footer {{ text-align:center; margin-top:2rem; font-size:0.9rem; color:#324551; /* primary */ }}
  </style>
</head>
<body>
  <div class="container">
    <h1>API Call Report</h1>
    <p><strong>Total Entries:</strong> {total}</p>

    <h2>By HTTP Method</h2>
    <table>
      <tr><th>Method</th><th>Count</th></tr>
      {''.join(f"<tr><td>{m}</td><td>{c}</td></tr>" for m,c in methods.items())}
    </table>

    <h2>By Endpoint</h2>
    <table>
      <tr><th>Endpoint</th><th>Count</th></tr>
      {''.join(f"<tr><td>{ep}</td><td>{c}</td></tr>" for ep,c in endpoints.items())}
    </table>

    <h2>By Base Path</h2>
    <table>
      <tr><th>Base Path</th><th>Count</th></tr>
      {''.join(f"<tr><td>/{b}/*</td><td>{c}</td></tr>" for b,c in bases.items())}
    </table>

    <footer>Made with ❤️ By Sid</footer> 
  </div>
</body>
</html>"""

def main():
    p = argparse.ArgumentParser(
        description="Generate a beautiful API-call report from Postman or Swagger/OpenAPI."
    )
    p.add_argument('-i','--input', required=True, help="JSON/YAML file")
    p.add_argument('-o','--output', default='report.html', help="Output HTML file")
    args = p.parse_args()

    raw = open(args.input, encoding='utf-8').read()
    data = yaml.safe_load(raw)

    if 'swagger' in data or 'openapi' in data:
        total, methods, endpoints, bases = parse_swagger(data)
    elif 'item' in data:
        total, methods, endpoints, bases = parse_postman(data)
    else:
        p.error("Unrecognized file format—must be Postman or OpenAPI.")

    html = generate_html(total, methods, endpoints, bases)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Report generated: {args.output}")

if __name__ == '__main__':
    main()
