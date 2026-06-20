import json, os, sys, urllib.request, base64, math
from urllib.request import Request, urlopen
from datetime import datetime, date
from collections import defaultdict

API_KEY = os.environ.get("WAKATIME_API_KEY", "")
if not API_KEY:
    print("WAKATIME_API_KEY not set")
    sys.exit(1)

auth = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {"Authorization": f"Basic {auth}"}
README_PATH = "README.md"
FIRST_YEAR = 2020

def fetch_summaries(start, end):
    url = f"https://wakatime.com/api/v1/users/current/summaries?start={start}&end={end}"
    req = Request(url, headers=HEADERS)
    try:
        resp = json.loads(urlopen(req, timeout=30).read())
        return resp.get("data", [])
    except Exception as e:
        print(f"Error fetching {start} to {end}: {e}")
        return []

def fetch_range(year_start, year_end):
    all_data = []
    for year in range(year_start, year_end + 1):
        s = f"{year}-01-01"
        e = f"{year}-12-31" if year < datetime.now().year else datetime.now().strftime("%Y-%m-%d")
        data = fetch_summaries(s, e)
        all_data.extend(data)
        print(f"  {year}: {len(data)} days")
    return all_data

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def find_earliest_date(data):
    for day in data:
        if day.get("grand_total", {}).get("total_seconds", 0) > 0:
            r = day.get("range", {})
            d = r.get("date", r.get("start", ""))
            if d:
                return d[:10]
    return "N/A"

def escape_svg(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

today = date.today()
start_year = FIRST_YEAR
end_year = today.year

print(f"Fetching WakaTime data from {start_year} to {end_year}...")
all_data = fetch_range(start_year, end_year)

if not all_data:
    print("No data found")
    sys.exit(0)

total_seconds = 0.0
languages = defaultdict(float)
projects = defaultdict(float)

for day in all_data:
    total_seconds += day.get("grand_total", {}).get("total_seconds", 0)
    for lang in day.get("languages", []):
        languages[lang["name"]] += lang.get("total_seconds", 0)
    for proj in day.get("projects", []):
        projects[proj["name"]] += proj.get("total_seconds", 0)

languages = dict(sorted(languages.items(), key=lambda x: -x[1]))
projects = dict(sorted(projects.items(), key=lambda x: -x[1]))

earliest = find_earliest_date(all_data)
total_formatted = format_time(total_seconds)

# Build SVG
BAR_W = 240
BAR_H = 8
BAR_X = 140
LABEL_W = 100
TIME_X = BAR_X + BAR_W + 15
PCT_X = TIME_X + 80
ROW_H = 24
COL1 = BAR_X + BAR_W + 15
COL2 = COL1 + 80

def svg_bar(name, secs, y):
    pct = (secs / total_seconds * 100) if total_seconds > 0 else 0
    bar_w = max(round(pct / 100 * BAR_W), 1) if pct > 0 else 1
    escaped = escape_svg(name)

    return f'''
  <text x="20" y="{y+6}" fill="#c8d6e5" font-family="'Courier New',monospace" font-size="12" font-weight="bold">{escaped}</text>
  <rect x="{BAR_X}" y="{y-4}" width="{BAR_W}" height="{BAR_H}" rx="4" fill="#151530"/>
  <rect x="{BAR_X}" y="{y-4}" width="{bar_w}" height="{BAR_H}" rx="4" fill="url(#barGrad)" filter="url(#glow)"/>
  <text x="{COL1}" y="{y+6}" fill="#a4b0be" font-family="'Courier New',monospace" font-size="11">{format_time(secs)}</text>
  <text x="{COL2}" y="{y+6}" fill="#00f5d4" font-family="'Courier New',monospace" font-size="12" font-weight="bold" filter="url(#glow)">{pct:.1f}%</text>'''

def svg_section(title, items, start_y):
    count = min(len(items), 8)
    h = 20 + count * ROW_H
    section = f'''
  <rect x="15" y="{start_y}" width="490" height="1" fill="url(#headerGrad)" opacity="0.4"/>
  <text x="20" y="{start_y+16}" fill="#48dbfb" font-family="'Courier New',monospace" font-size="10" letter-spacing="2">▸ {title}</text>'''
    for i, (name, secs) in enumerate(list(items.items())[:8]):
        section += svg_bar(name, secs, start_y + 32 + i * ROW_H)
    return section, h

lang_count = min(len(languages), 8)
proj_count = min(len(projects), 8)
lang_h = 20 + lang_count * ROW_H
proj_h = 20 + proj_count * ROW_H
separator = 20
total_h = 90 + lang_h + separator + proj_h + 25

SVG = f'''<svg width="520" viewBox="0 0 520 {total_h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#00f5d4"/>
      <stop offset="50%" stop-color="#48dbfb"/>
      <stop offset="100%" stop-color="#b5179e"/>
    </linearGradient>
    <linearGradient id="headerGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00f5d4" stop-opacity="0"/>
      <stop offset="30%" stop-color="#00f5d4" stop-opacity="1"/>
      <stop offset="70%" stop-color="#48dbfb" stop-opacity="1"/>
      <stop offset="100%" stop-color="#b5179e" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00f5d4"/>
      <stop offset="50%" stop-color="#48dbfb"/>
      <stop offset="100%" stop-color="#b5179e"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="520" height="{total_h}" rx="14" fill="#06061a"/>
  <rect x="1" y="1" width="518" height="{total_h-2}" rx="13" fill="none" stroke="url(#accent)" stroke-width="0.5" opacity="0.3"/>

  <text x="260" y="34" text-anchor="middle" fill="#00f5d4" font-family="'Courier New',monospace" font-size="20" font-weight="bold" filter="url(#glow)" letter-spacing="3">⚡ WAKATIME  STATS</text>

  <text x="260" y="54" text-anchor="middle" fill="#ffffff" font-family="'Courier New',monospace" font-size="10" opacity="0.8">{total_formatted}  ·  coding activity</text>

  <text x="260" y="70" text-anchor="middle" fill="#576574" font-family="'Courier New',monospace" font-size="9">{earliest}  →  {today}</text>'''

lang_svg, _ = svg_section("LANGUAGES", languages, 90)
SVG += lang_svg

proj_start = 90 + lang_h + separator
proj_svg, _ = svg_section("PROJECTS", projects, proj_start)
SVG += proj_svg

SVG += f'''
  <line x1="20" y1="{total_h-10}" x2="500" y2="{total_h-10}" stroke="url(#headerGrad)" stroke-width="0.5" opacity="0.3"/>
</svg>'''

SVG_FILE = "wakatime-stats.svg"
with open(SVG_FILE, "w") as f:
    f.write(SVG)
print(f"Saved SVG ({total_h}px tall)")

output = '<div align="center">\n\n<img src="wakatime-stats.svg" alt="WakaTime Stats" width="520">\n\n</div>'

# Update README
if not os.path.exists(README_PATH):
    print(f"{README_PATH} not found")
    sys.exit(1)

with open(README_PATH, "r") as f:
    content = f.read()

start_marker = "<!--START_SECTION:waka-->"
end_marker = "<!--END_SECTION:waka-->"

if start_marker in content and end_marker in content:
    start_idx = content.index(start_marker) + len(start_marker)
    end_idx = content.index(end_marker)
    new_content = content[:start_idx] + "\n\n" + output + "\n\n" + content[end_idx:]
    with open(README_PATH, "w") as f:
        f.write(new_content)
    print("README updated successfully")
else:
    print(f"Markers not found in {README_PATH}")
    sys.exit(1)
