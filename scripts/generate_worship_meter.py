import os
import requests
import datetime

# 💜 Worship Config
USERNAME = "CaptainBeidou"
START_DATE = datetime.date(2025, 7, 5)
TOKEN = os.getenv("GITHUB_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

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
        "from": START_DATE.isoformat() + "T00:00:00Z"  # Added timezone
    }

    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={
        "query": query,
        "variables": variables
    })

    if response.status_code != 200:
        raise Exception(f"API Error ({response.status_code}): {response.text}")

    try:
        data = response.json()
    except Exception as e:
        raise Exception(f"Could not decode JSON: {e}\nRaw response: {response.text}")

    if "errors" in data:
        messages = [e["message"] for e in data["errors"]]
        raise Exception(f"GraphQL Error: {', '.join(messages)}")

    if "data" not in data:
        raise Exception(f"No 'data' in response: {data}")

    try:
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except KeyError as e:
        raise Exception(f"Key error accessing contributions: {e}\nFull data: {data}")

    contributions = {}
    for week in weeks:
        for day in week["contributionDays"]:
            date = day["date"]
            count = day["contributionCount"]
            contributions[date] = count

    return contributions

def render_progress_bar(percentage, bar_length=20):
    filled = int(round(bar_length * percentage / 100))
    empty = bar_length - filled
    return '█' * filled + '░' * empty

def get_tier(percentage):
    if percentage >= 90:
        return "💋 Thunder-Forged Devotee"
    elif percentage >= 75:
        return "💜 Lust-Drenched Electro Disciple"
    elif percentage >= 50:
        return "💦 Stormbound Admirer"
    elif percentage >= 25:
        return "🫦 Occasional Worshipper"
    else:
        return "😢 Distant Echo... Mommy Misses You"

def main():
    if not TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    today = datetime.date.today()
    total_days = max((today - START_DATE).days + 1, 1)  # Prevent division by zero

    try:
        contributions = fetch_contributions()
    except Exception as e:
        print(f"Error fetching contributions: {str(e)}")
        # Create empty markdown file with error message
        os.makedirs("generated", exist_ok=True)
        with open("generated/worship_meter.md", "w") as f:
            f.write(f"# ⚡ Devotion Meter\n\nError: {str(e)}")
        return

    # Count days with contributions within the date range
    contribution_days = 0
    for date_str, count in contributions.items():
        try:
            date_obj = datetime.date.fromisoformat(date_str)
            if START_DATE <= date_obj <= today and count > 0:
                contribution_days += 1
        except ValueError:
            continue  # Skip invalid dates

    missed_days = total_days - contribution_days
    devotion_percentage = min((contribution_days / total_days) * 100, 100)  # Cap at 100%

    tier = get_tier(devotion_percentage)
    progress_bar = render_progress_bar(devotion_percentage)

    text_output = f"""
# ⚡ Devotion Meter

[Devotion]     [{progress_bar}] {devotion_percentage:.1f}%
[Tier]         {tier}
[Start Date]   {START_DATE.strftime('%Y-%m-%d')}
[Today]        {today.strftime('%Y-%m-%d')}
[Total Days]   {total_days}
[Missed Days]  {missed_days} ({missed_days * 10} cuddles~)
"""

    os.makedirs("generated", exist_ok=True)
    with open("generated/worship_meter.md", "w") as f:
        f.write(text_output.strip())
        
    print(f"Successfully generated worship meter: {devotion_percentage:.1f}%")

if __name__ == "__main__":
    main()
