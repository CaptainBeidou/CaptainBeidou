import os
import requests
import datetime

USERNAME = "CaptainBeidou"
START_DATE = datetime.date(2025, 7, 5)
TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}

GRAPHQL_URL = "https://api.github.com/graphql"

def fetch_contributions():
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
        "from": START_DATE.isoformat()
    }

    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={
        "query": query,
        "variables": variables
    })

    if response.status_code != 200:
        raise Exception(f"GitHub API returned HTTP {response.status_code}: {response.text}")

    data = response.json()

    if "errors" in data:
        raise Exception(f"GraphQL error: {data['errors']}")

    try:
        days = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except KeyError:
        raise Exception(f"Unexpected response structure: {data}")

    contributions = {}
    for week in days:
        for day in week["contributionDays"]:
            date = day["date"]
            count = day["contributionCount"]
            contributions[date] = count

    return contributions

def calculate_devotion(contributions):
    today = datetime.date.today()
    total_days = (today - START_DATE).days + 1
    committed_days = sum(1 for date, count in contributions.items() if count > 0)
    percentage = int((committed_days / total_days) * 100)
    return percentage

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
    bar_width = int(percentage * 3)
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
    contributions = fetch_contributions()
    devotion = calculate_devotion(contributions)
    tier = get_tier(devotion)
    generate_svg(devotion, tier)
