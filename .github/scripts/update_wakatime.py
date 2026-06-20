import json, os, sys, urllib.request, base64
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

def make_bar(percent, width=20):
    filled = round(percent / 100 * width)
    return "█" * filled + "░" * (width - filled)

def find_earliest_date(data):
    for day in data:
        r = day.get("range", {})
        d = r.get("date", r.get("start", ""))
        if d:
            return d[:10]
    return "N/A"

today = date.today()
start_year = FIRST_YEAR
end_year = today.year

print(f"Fetching WakaTime data from {start_year} to {end_year}...")
all_data = fetch_range(start_year, end_year)

if not all_data:
    print("No data found")
    sys.exit(0)

# Aggregate
total_seconds = 0.0
languages = defaultdict(float)
projects = defaultdict(float)

for day in all_data:
    total_seconds += day.get("grand_total", {}).get("total_seconds", 0)
    for lang in day.get("languages", []):
        languages[lang["name"]] += lang.get("total_seconds", 0)
    for proj in day.get("projects", []):
        projects[proj["name"]] += proj.get("total_seconds", 0)

# Sort by time descending
languages = dict(sorted(languages.items(), key=lambda x: -x[1]))
projects = dict(sorted(projects.items(), key=lambda x: -x[1]))

earliest = find_earliest_date(all_data)
total_formatted = format_time(total_seconds)

# Format markdown
lines = []
lines.append(f"**From:** {earliest} — **To:** {today}")
lines.append("")
lines.append(f"**Total Time:** {total_formatted}")
lines.append("")

if languages:
    lines.append("**Languages:**")
    for name, secs in list(languages.items())[:8]:
        pct = (secs / total_seconds * 100) if total_seconds > 0 else 0
        bar = make_bar(pct)
        lines.append(f"- {name:<12} {format_time(secs):>8}  {bar}  {pct:.1f}%")
    lines.append("")

if projects:
    lines.append("**Projects:**")
    for name, secs in list(projects.items())[:8]:
        pct = (secs / total_seconds * 100) if total_seconds > 0 else 0
        bar = make_bar(pct)
        lines.append(f"- {name:<20} {format_time(secs):>8}  {bar}  {pct:.1f}%")
    lines.append("")

output = "\n".join(lines)
print(f"\nGenerated:\n{output}")

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
    new_content = content[:start_idx] + "\n\n```text\n" + output + "\n```\n\n" + content[end_idx:]
    with open(README_PATH, "w") as f:
        f.write(new_content)
    print(f"\nREADME updated successfully")
else:
    print(f"Markers not found in {README_PATH}")
    sys.exit(1)
