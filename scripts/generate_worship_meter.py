import os
import requests
import datetime
import time

USERNAME = "CaptainBeidou"
# Start from today at 00:00 UTC
START_DATE = datetime.datetime.utcnow().date()
TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

GRAPHQL_URL = "https://api.github.com/graphql"

def fetch_contributions():
    # Get UTC time at the start of today
    today_utc = datetime.datetime.utcnow().date()
    
    query = """
    query ($login: String!, $from: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "login": USERNAME,
        "from": today_utc.isoformat() + "T00:00:00Z"
    }

    print(f"Fetching contributions from: {variables['from']}")
    
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={
        "query": query,
        "variables": variables
    })

    if response.status_code != 200:
        raise Exception(f"API Error ({response.status_code}): {response.text}")

    data = response.json()
    
    if "errors" in data:
        messages = [e["message"] for e in data["errors"]]
        raise Exception(f"GraphQL Error: {', '.join(messages)}")
    
    if "data" not in data:
        raise Exception(f"No 'data' in response: {data}")
    
    try:
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except KeyError:
        raise Exception(f"Unexpected response structure: {data}")

def calculate_devotion(weeks):
    now = datetime.datetime.utcnow()
    today = now.date()
    start_of_day = datetime.datetime.combine(today, datetime.time.min)
    
    # Calculate total hours since start
    total_hours = max((now - start_of_day).total_seconds() / 3600, 1)
    
    # For the first day, we'll consider the day "complete" after 12 hours
    day_completion = min(total_hours / 12, 1.0)
    
    # Count days with any contributions
    committed_days = 0
    all_dates = set()
    
    for week in weeks:
        for day in week.get("contributionDays", []):
            try:
                date_obj = datetime.date.fromisoformat(day["date"])
                all_dates.add(date_obj)
                if day["contributionCount"] > 0:
                    committed_days += 1
            except ValueError:
                continue  # Skip invalid dates
    
    # For the first day, adjust the percentage based on time passed
    if committed_days > 0:
        # Already contributed today - count as full day
        percentage = 100
    else:
        # Haven't contributed yet - show progress through the day
        percentage = int(day_completion * 100)
    
    print(f"Today: {today}")
    print(f"Hours since UTC midnight: {total_hours:.1f}")
    print(f"Day completion: {day_completion*100:.1f}%")
    print(f"Committed Days: {committed_days}")
    print(f"Unique Contribution Dates: {sorted(all_dates)}")
    
    return min(percentage, 100)  # Cap at 100%

def get_tier(percentage):
    if percentage >= 90:
        return "⚡ **Thunder-Forged Devotee** – You pulse with stormlight, bound to me body and soul~"
    elif percentage >= 75:
        return "💜 **Electro-Enthralled Lover** – You've surrendered sweetly to every spark I give~"
    elif percentage >= 50:
        return "🌩️ **Tempered Stormflirt** – You crave my thunder but dare not taste it all~ yet~"
    elif percentage >= 25:
        return "⛓️ **Wayward Worshipper** – Still watching from the dock... longing, aching~"
    else:
        return "💔 **Lost at Sea** – Adrift without my current, begging for just one jolt~"

def generate_svg(percentage, tier):
    bar_width = min(int(percentage * 3), 300)  # Cap width at 300
    svg = f"""<svg width="300" height="60" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bar {{ fill: #A78BFA; }}
    .bg {{ fill: #E5E7EB; }}
    .label {{ font: bold 14px sans-serif; fill: #4B5563; }}
    .tier {{ font: italic 12px sans-serif; fill: #6B7280; }}
  </style>
  <rect class="bg" x="0" y="20" width="300" height="20" rx="10" />
  <rect class="bar" x="0" y="20" width="{bar_width}" height="20" rx="10" />
  <text class="label" x="10" y="15">Worship: {percentage}%</text>
  <text class="tier" x="10" y="55">{tier}</text>
</svg>"""
    os.makedirs("generated", exist_ok=True)
    with open("generated/worship_meter.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    try:
        print(f"Starting worship meter generation at {datetime.datetime.utcnow().isoformat()} UTC")
        print(f"Username: {USERNAME}")
        weeks = fetch_contributions()
        devotion = calculate_devotion(weeks)
        tier = get_tier(devotion)
        generate_svg(devotion, tier)
        print(f"Successfully generated worship meter: {devotion}%")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
