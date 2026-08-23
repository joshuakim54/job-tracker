import json
import os
import requests

# Reads secret from GitHub Actions environment variable (or falls back to local value)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_LOCAL_WEBHOOK_IF_TESTING")

# Target company slugs and ATS types
TARGET_COMPANIES = {
    # Greenhouse: boards-api.greenhouse.io/v1/boards/{slug}/jobs
    "stripe": "greenhouse",
    "databricks": "greenhouse",
    "figma": "greenhouse",
    # Lever: api.lever.co/v0/postings/{slug}
    "palantir": "lever",
    "netflix": "lever",
}

# Case-insensitive title filters. Leave empty [] to receive all jobs.
TITLE_KEYWORDS = ["engineer", "developer", "data", "product", "analyst"]

HISTORY_FILE = "seen_jobs.json"


def fetch_greenhouse_jobs(company_slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return []
        data = res.json()
        return [
            {
                "id": f"gh_{item['id']}",
                "company": company_slug.capitalize(),
                "title": item.get("title", "Unknown"),
                "location": item.get("location", {}).get("name", "Remote/Unspecified"),
                "url": item.get("absolute_url", ""),
            }
            for item in data.get("jobs", [])
        ]
    except Exception as e:
        print(f"Error fetching Greenhouse ({company_slug}): {e}")
        return []


def fetch_lever_jobs(company_slug):
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return []
        data = res.json()
        return [
            {
                "id": f"lever_{item['id']}",
                "company": company_slug.capitalize(),
                "title": item.get("text", "Unknown"),
                "location": item.get("categories", {}).get("location", "Remote/Unspecified"),
                "url": item.get("hostedUrl", ""),
            }
            for item in data
        ]
    except Exception as e:
        print(f"Error fetching Lever ({company_slug}): {e}")
        return []


def send_discord_alert(job):
    payload = {
        "username": "Job Monitor Bot",
        "embeds": [
            {
                "title": f"🚨 New Job: {job['title']}",
                "url": job["url"],
                "color": 3066993,  # Green
                "fields": [
                    {"name": "Company", "value": job["company"], "inline": True},
                    {"name": "Location", "value": job["location"], "inline": True},
                ],
                "footer": {"text": "ATS Automated Monitor"},
            }
        ],
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)


def load_seen_jobs():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen_ids):
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def main():
    seen_ids = load_seen_jobs()
    new_jobs_found = []

    for company, board_type in TARGET_COMPANIES.items():
        if board_type == "greenhouse":
            jobs = fetch_greenhouse_jobs(company)
        elif board_type == "lever":
            jobs = fetch_lever_jobs(company)
        else:
            continue

        for job in jobs:
            if job["id"] in seen_ids:
                continue

            if TITLE_KEYWORDS:
                title_lower = job["title"].lower()
                if not any(kw.lower() in title_lower for kw in TITLE_KEYWORDS):
                    continue

            new_jobs_found.append(job)
            seen_ids.add(job["id"])

    for job in new_jobs_found:
        print(f"Alerting: {job['company']} - {job['title']}")
        send_discord_alert(job)

    save_seen_jobs(seen_ids)
    print(f"Finished check. Sent {len(new_jobs_found)} alert(s).")


if __name__ == "__main__":
    main()
