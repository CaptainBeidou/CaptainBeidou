import datetime
import os
import requests

# === CONFIG ===
USERNAME = "CaptainBeidou"
START_DATE = datetime.date(2025, 7, 5)
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT_PATH = "generated/worship_meter.svg"

# Devotion tiers
TIERS = [
    (0, "💧 Deckhand in Denial"),
    (20, "⚒️ Cuddlesmith Apprentice"),
    (40, "⚡ Electro Admirer"),
    (60, "🔥 Passionate First Mate"),
    (80, "🌩️ Stormbound Soulmate"),
    (100, "👑 Devotion Eternal")
]

# Today's date
today = datetime.date.today()
total_days = (today - START_DATE).days + 1

# Fetch recent commit days (via public PushEvents API)
def get_commit_days(username, token):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/users/{username}/events/public"
    commit_days = set()
    for page in range(1, 11):  # up to 10 pages
        r = requests.get(f"{url}?page={page}", headers=headers)
        if r.status_code != 200:
            break
        for event in r.json():
            if event["type"] == "PushEvent":
                date_str = event["created_at"][:10]
                day = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if day >= START_DATE:
                    commit_days.add(day)
    return commit_days

commit_days = get_commit_days(USERNAME, TOKEN)
devotion = min(100, round((len(commit_days) / total_days) * 100))

# Get devotion tier
tier = max((label for pct, label in TIERS if devotion >= pct), key=lambda l: next(p for p, t in TIERS if t == l))

# Generate SVG
bar_width = devotion * 3  # bar width max = 300
svg = f"""<svg width="320" height="90" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="20" fill="#eee" rx="10"/>
  <rect width="{bar_width}" height="20" fill="#9333ea" rx="10"/>
  <text x="10" y="50" font-family="sans-serif" font-size="14" fill="#333">Devotion: {devotion}%</text>
  <text x="10" y="70" font-family="sans-serif" font-size="16" fill="#9333ea">{tier}</text>
</svg>
"""

# Save SVG
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write(svg)
