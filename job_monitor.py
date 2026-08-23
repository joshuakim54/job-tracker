import json
import os
import requests

# ==========================================
# CONFIGURATION & SECRETS
# ==========================================
# Reads webhook from GitHub Actions secrets or local environment variable
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")

# Companies to monitor
# Companies to monitor mapped to their ATS type
TARGET_COMPANIES = {
    # ----------------------------------------------------
    # 1. LOCAL RALEIGH / DURHAM / RTP TECH HUBS
    # ----------------------------------------------------
    "pendo": {
        "type": "greenhouse",
        "slug": "pendo",
        "display_name": "Pendo (Raleigh HQ)",
    },
    "redhat": {
        "type": "greenhouse",
        "slug": "redhat",
        "display_name": "Red Hat (Raleigh HQ)",
    },
    "epicgames": {
        "type": "lever",
        "slug": "epicgames",
        "display_name": "Epic Games (Cary HQ)",
    },
    "cisco": {
        "type": "workday",
        "domain": "cisco.wd1.myworkdayjobs.com",
        "tenant": "cisco",
        "career_site": "Cisco_Careers",
        "display_name": "Cisco (RTP Campus)",
    },
    "lenovo": {
        "type": "workday",
        "domain": "lenovo.wd3.myworkdayjobs.com",
        "tenant": "lenovo",
        "career_site": "External",
        "display_name": "Lenovo (Morrisville HQ)",
    },
    # ----------------------------------------------------
    # 2. TECH & INFRASTRUCTURE GIANTS (US Remote / RTP Hubs)
    # ----------------------------------------------------
    "stripe": {
        "type": "greenhouse",
        "slug": "stripe",
        "display_name": "Stripe",
    },
    "databricks": {
        "type": "greenhouse",
        "slug": "databricks",
        "display_name": "Databricks",
    },
    "cloudflare": {
        "type": "greenhouse",
        "slug": "cloudflare",
        "display_name": "Cloudflare",
    },
    "palantir": {
        "type": "lever",
        "slug": "palantir",
        "display_name": "Palantir",
    },
    "netflix": {
        "type": "lever",
        "slug": "netflix",
        "display_name": "Netflix",
    },
    "nvidia": {
        "type": "workday",
        "domain": "nvidia.wd5.myworkdayjobs.com",
        "tenant": "nvidia",
        "career_site": "NVIDIAExternalCareerSite",
        "display_name": "NVIDIA",
    },
    "salesforce": {
        "type": "workday",
        "domain": "salesforce.wd1.myworkdayjobs.com",
        "tenant": "salesforce",
        "career_site": "External_Career_Site",
        "display_name": "Salesforce",
    },
    "ibm": {
        "type": "workday",
        "domain": "ibm.wd5.myworkdayjobs.com",
        "tenant": "ibm",
        "career_site": "External",
        "display_name": "IBM (RTP Campus)",
    },
    # ----------------------------------------------------
    # 3. HIGH-GROWTH UNICORNS & DEVELOPER TOOLS (US Remote)
    # ----------------------------------------------------
    "figma": {
        "type": "greenhouse",
        "slug": "figma",
        "display_name": "Figma",
    },
    "datadog": {
        "type": "greenhouse",
        "slug": "datadog",
        "display_name": "Datadog",
    },
    "mongodb": {
        "type": "greenhouse",
        "slug": "mongodb",
        "display_name": "MongoDB",
    },
    "hashicorp": {
        "type": "greenhouse",
        "slug": "hashicorp",
        "display_name": "HashiCorp",
    },
    "elastic": {
        "type": "greenhouse",
        "slug": "elastic",
        "display_name": "Elastic",
    },
    "cockroachlabs": {
        "type": "greenhouse",
        "slug": "cockroachlabs",
        "display_name": "Cockroach Labs",
    },
    "atlassian": {
        "type": "lever",
        "slug": "atlassian",
        "display_name": "Atlassian",
    },
}
HISTORY_FILE = "seen_jobs.json"

# ==========================================
# TARGETING PARAMETERS (Mid-Level SWE in RTP / US Remote)
# ==========================================

# 1. SOFTWARE ENGINEERING TITLES
TITLE_INCLUDE = [
    "software engineer",
    "software development engineer",
    "sde",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "fullstack engineer",
    "systems engineer",
    "platform engineer",
    "infrastructure engineer",
    "application engineer",
]

# Exclude entry-level/internships and high-level management
TITLE_EXCLUDE = [
    "intern",
    "internship",
    "co-op",
    "coop",
    "university grad",
    "new grad",
    "entry level",
    "distinguished",
    "director",
    "vp",
    "head of",
    "manager",
]

# 2. LOCATIONS (RTP Region + US Remote)
LOCATION_INCLUDE = [
    "research triangle",
    "rtp",
    "raleigh",
    "durham",
    "chapel hill",
    "morrisville",
    "cary",
    "remote",
    "us remote",
    "remote - us",
    "united states",
    "us",
    "boston",
    "nyc"
]

# Exclude non-US locations (e.g., Remote Europe/APAC)
LOCATION_EXCLUDE = [
    "uk",
    "london",
    "europe",
    "emea",
    "apac",
    "canada",
    "india",
    "latam",
    "germany",
    "japan",
    "australia",
]


# ==========================================
# MATCHING LOGIC
# ==========================================
def is_matching_job(job):
    title = job["title"].lower()
    location = job["location"].lower()

    # --- Title Filtering ---
    if not any(kw in title for kw in TITLE_INCLUDE):
        return False

    if any(kw in title for kw in TITLE_EXCLUDE):
        return False

    # --- Location Filtering ---
    if not any(loc in location for loc in LOCATION_INCLUDE):
        return False

    if any(loc in location for loc in LOCATION_EXCLUDE):
        return False

    return True


# ==========================================
# API FETCHERS
# ==========================================
def fetch_greenhouse_jobs(company_slug):
    """Fetch public jobs from Greenhouse ATS."""
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
                "title": item.get("title", "Unknown Title"),
                "location": item.get("location", {}).get("name", "Remote/Unspecified"),
                "url": item.get("absolute_url", ""),
            }
            for item in data.get("jobs", [])
        ]
    except Exception as e:
        print(f"Error fetching Greenhouse for {company_slug}: {e}")
        return []


def fetch_lever_jobs(company_slug):
    """Fetch public jobs from Lever ATS."""
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
                "title": item.get("text", "Unknown Title"),
                "location": item.get("categories", {}).get("location", "Remote/Unspecified"),
                "url": item.get("hostedUrl", ""),
            }
            for item in data
        ]
    except Exception as e:
        print(f"Error fetching Lever for {company_slug}: {e}")
        return []
def fetch_workday_jobs(company_key, config):
    """Fetch public jobs from Workday ATS."""
    domain = config["domain"]
    tenant = config["tenant"]
    career_site = config["career_site"]
    display_name = config.get("display_name", company_key.capitalize())

    url = f"https://{domain}/wday/cxs/{tenant}/{career_site}/jobs"
    
    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "Software Engineer"  # Initial filter to optimize Workday response payload
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        
        data = res.json()
        jobs = []
        for item in data.get("jobPostings", []):
            external_path = item.get("externalPath", "")
            job_url = f"https://{domain}/en-US/{career_site}{external_path}" if external_path else f"https://{domain}"
            
            # Use externalPath or title as unique ID
            job_id_suffix = external_path.replace("/", "_") if external_path else item.get("title", "")
            
            jobs.append({
                "id": f"wd_{tenant}_{job_id_suffix}",
                "company": display_name,
                "title": item.get("title", "Unknown Title"),
                "location": item.get("locationsText", "Remote/Unspecified"),
                "url": job_url,
            })
        return jobs
    except Exception as e:
        print(f"Error fetching Workday for {tenant}: {e}")
        return []


# ==========================================
# DISCORD NOTIFIER
# ==========================================
def send_discord_alert(job):
    """Sends a rich formatted embed message to Discord."""
    payload = {
        "username": "SWE Job Alert Bot",
        "embeds": [
            {
                "title": f"🚨 New Role: {job['title']}",
                "url": job["url"],
                "color": 3066993,  # Green
                "fields": [
                    {"name": "Company", "value": job["company"], "inline": True},
                    {"name": "Location", "value": job["location"], "inline": True},
                ],
                "footer": {"text": "Greenhouse/Lever Monitor"},
            }
        ],
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending Discord webhook: {e}")


# ==========================================
# STATE MANAGEMENT & MAIN LOOP
# ==========================================
def load_seen_jobs():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()


def save_seen_jobs(seen_ids):
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def main():
    seen_ids = load_seen_jobs()
    new_jobs_found = []

    print("Starting job search...")

    for company, board_type in TARGET_COMPANIES.items():
        if board_type == "greenhouse":
            jobs = fetch_greenhouse_jobs(company)
        elif board_type == "lever":
            jobs = fetch_lever_jobs(company)
        else:
            continue

        for job in jobs:
            # Skip if already stored in history
            if job["id"] in seen_ids:
                continue

            # Check role & location criteria
            if not is_matching_job(job):
                continue

            new_jobs_found.append(job)
            seen_ids.add(job["id"])

    # Dispatch Discord alerts
    for job in new_jobs_found:
        print(f"Matched: [{job['company']}] {job['title']} - {job['location']}")
        send_discord_alert(job)

    # Save state
    save_seen_jobs(seen_ids)
    print(f"Job check finished. Sent {len(new_jobs_found)} alert(s).")


if __name__ == "__main__":
    main()
