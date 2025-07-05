import os
import requests
import datetime
from datetime import timezone

# 💜 Worship Config
USERNAME = "CaptainBeidou"
TOKEN = os.getenv("GITHUB_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def fetch_contributions(start_date, end_date):
    query = """
    query ($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
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
        "from": start_date.isoformat() + "T00:00:00Z",
        "to": end_date.isoformat() + "T23:59:59Z"
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
    percentage = max(0, min(percentage, 100))
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
    
    # Use timezone-aware datetime
    now_utc = datetime.datetime.now(timezone.utc)
    today = now_utc.date()
    timestamp = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Calculate first day of current month
    first_day_of_month = today.replace(day=1)
    
    # Calculate days in month
    if today.month == 12:
        last_day_of_month = today.replace(day=31)
    else:
        last_day_of_month = today.replace(month=today.month+1, day=1) - datetime.timedelta(days=1)
    
    total_days_in_month = (last_day_of_month - first_day_of_month).days + 1
    days_so_far = (today - first_day_of_month).days + 1

    try:
        contributions = fetch_contributions(first_day_of_month, today)
    except Exception as e:
        print(f"Error fetching contributions: {str(e)}")
        os.makedirs("generated", exist_ok=True)
        with open("generated/worship_meter.md", "w", encoding="utf-8") as f:
            f.write(f"# ⚡ Monthly Devotion Meter\n\nError: {str(e)}\n\nGenerated at {timestamp}")
        return

    # Count days with contributions this month
    contribution_days = 0
    current_date = first_day_of_month
    
    # Iterate through all dates from first day of month to today (inclusive)
    while current_date <= today:
        date_iso = current_date.isoformat()
        count = contributions.get(date_iso, 0)
        if count > 0:
            contribution_days += 1
        current_date += datetime.timedelta(days=1)

    missed_days = days_so_far - contribution_days
    devotion_percentage = min((contribution_days / days_so_far) * 100, 100) if days_so_far > 0 else 0

    tier = get_tier(devotion_percentage)
    progress_bar = render_progress_bar(devotion_percentage)

    # Add timestamp to ensure unique content
    text_output = f"""# ⚡ Monthly Devotion Meter

[Month]        {today.strftime('%B %Y')}

[Devotion]     [{progress_bar}] {devotion_percentage:.1f}%

[Tier]         {tier}

[Start Date]   {first_day_of_month.strftime('%Y-%m-%d')}

[Today]        {today.strftime('%Y-%m-%d')}

[Days So Far]  {days_so_far} of {total_days_in_month}

[Missed Days]  {missed_days} ({missed_days * 10} cuddles~)

*Generated at {timestamp}*
"""

    os.makedirs("generated", exist_ok=True)
    with open("generated/worship_meter.md", "w", encoding="utf-8") as f:
        f.write(text_output.strip())
        
    print(f"Successfully generated monthly devotion meter: {devotion_percentage:.1f}% at {timestamp}")

if __name__ == "__main__":
    main()
