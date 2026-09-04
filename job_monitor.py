import time
import json
import os
import re
import shutil
import argparse
from html import unescape
from urllib.parse import quote_plus
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# CONFIGURATION & SECRETS
# ==========================================
# Reads webhook from GitHub Actions secrets or local environment variable
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.getenv("HISTORY_FILE", os.path.join(BASE_DIR, "seen_jobs.local.json"))
JOBS_CACHE_FILE = os.getenv("JOBS_CACHE_FILE", os.path.join(BASE_DIR, "jobs_cache.json"))
COMPANIES_FILE = os.path.join(BASE_DIR, "companies.json")

# Pre-compiled regex patterns for performance
REGEX_WORD_BOUNDARY = r"(?<!\w){}(?!\w)"
REGEX_NORMALIZE = re.compile(r"[^a-z0-9]+")
REGEX_TAG_REMOVAL = re.compile(r"<[^>]+>")
REGEX_ICIMS_CARD = re.compile(r'<li class="iCIMS_JobCardItem">(.*?)</li>', re.S)
REGEX_ICIMS_TITLE = re.compile(r'<a href="([^"]+/jobs/[^" ]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>', re.S | re.I)
REGEX_ICIMS_LOCATION = re.compile(r'<dd class="iCIMS_JobHeaderData"[^>]*>.*?<span[^>]*>\s*(.*?)\s*</span>', re.S | re.I)
REGEX_ICIMS_JOB_ID = re.compile(r"/jobs/(\d+)")


def discord_is_configured():
    return bool(DISCORD_WEBHOOK_URL) and DISCORD_WEBHOOK_URL != "YOUR_DISCORD_WEBHOOK_URL_HERE"


def load_target_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        companies = json.load(f)

    if not isinstance(companies, dict):
        raise ValueError("companies.json must contain an object of company configurations")

    return companies


TARGET_COMPANIES = load_target_companies()

# ==========================================
# TARGETING PARAMETERS
# ==========================================

TITLE_INCLUDE = [
    "software engineer",
    "software engineering",
    "software development engineer",
    "software engineering intern",
    "software engineer intern",
    "software developer intern",
    "engineering intern",
    "sde",
    "sw engineer",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "systems engineer",
    "platform engineer",
    "infrastructure engineer",
    "developer",
]

# Excludes high-level executive management
TITLE_EXCLUDE = [
    "principal",
    "distinguished",
    "director",
    "vp",
    "head of",
    "manager",
]

LOCATION_INCLUDE = [
    "research triangle",
    "rtp",
    "raleigh",
    "durham",
    "chapel hill",
    "morrisville",
    "cary",
    "nc",
    "north carolina",
    "boston",
    "massachusetts",
    "mass",
    "ma",
    "remote",
    "united states",
    "usa",
    "us -",
]

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
    "paris",
    "france",
    "lithuania",
    "china",
    "denmark"
]

US_LOCATION_MARKERS = [
    "united states",
    "usa",
    "us",
    "alabama", "alaska", "arizona", "arkansas", "california",
    "colorado", "connecticut", "delaware", "florida", "georgia",
    "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas",
    "kentucky", "louisiana", "maine", "maryland", "massachusetts",
    "michigan", "minnesota", "mississippi", "missouri", "montana",
    "nebraska", "nevada", "new hampshire", "new jersey", "new mexico",
    "new york", "north carolina", "north dakota", "ohio", "oklahoma",
    "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
    # Major US tech hubs, cities, and regions
    "san francisco", "sf", "bay area", "silicon valley", "san jose", "sunnyvale",
    "mountain view", "palo alto", "redwood city", "menlo park", "oakland",
    "seattle", "bellevue", "redmond", "austin", "dallas", "houston", "san antonio",
    "chicago", "new york city", "nyc", "manhattan", "brooklyn",
    "boston", "cambridge", "los angeles", "la", "san diego", "denver", "boulder",
    "atlanta", "philadelphia", "philly", "pittsburgh", "washington dc", "dc",
    "arlington", "reston", "mclean", "baltimore", "minneapolis", "salt lake city",
    "slc", "phoenix", "tempe", "portland", "miami", "orlando", "tampa", "nashville",
    "raleigh", "durham", "chapel hill", "cary", "morrisville", "charlotte",
    "rtp", "research triangle",
]


# Pre-compile location regexes
_LOCATION_EXCLUDE_REGEX = [re.compile(REGEX_WORD_BOUNDARY.format(re.escape(term))) for term in LOCATION_EXCLUDE]
_US_LOCATION_MARKERS_REGEX = [re.compile(REGEX_WORD_BOUNDARY.format(re.escape(term))) for term in US_LOCATION_MARKERS]
_REMOTE_REGEX = re.compile(REGEX_WORD_BOUNDARY.format("remote|anywhere|worldwide|global"))

# ==========================================
# MATCHING LOGIC
# ==========================================
def is_us_location(location):
    normalized_location = REGEX_NORMALIZE.sub(" ", str(location).lower()).strip()
    if not normalized_location:
        return False

    # Check for US markers
    has_us_marker = any(regex.search(normalized_location) for regex in _US_LOCATION_MARKERS_REGEX)
    if not has_us_marker:
        return False

    # Check for excluded international locations (exclude unless a US marker is explicitly present in multi-location list)
    has_excluded = any(regex.search(normalized_location) for regex in _LOCATION_EXCLUDE_REGEX)
    if has_excluded and not has_us_marker:
        return False

    return True


def is_matching_job(job):
    title = job["title"].lower()
    location = job["location"].lower()

    # Title check
    if not any(kw in title for kw in TITLE_INCLUDE):
        return False

    if any(kw in title for kw in TITLE_EXCLUDE):
        return False

    # Location check - must be US and in LOCATION_INCLUDE list
    if not is_us_location(location):
        return False
    
    # Must match at least one location in LOCATION_INCLUDE
    if not any(contains_term(location, term) for term in LOCATION_INCLUDE):
        return False

    return True


def contains_term(text, term):
    """Check if term appears as a word boundary match in text."""
    normalized_text = REGEX_NORMALIZE.sub(" ", str(text).lower()).strip()
    normalized_term = REGEX_NORMALIZE.sub(" ", str(term).lower()).strip()
    if not normalized_term:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", normalized_text) is not None


# ==========================================
# API FETCHERS
# ==========================================
def fetch_greenhouse_jobs(company_key, config):
    """Fetch public jobs from Greenhouse ATS."""
    slug = config["slug"]
    display_name = config.get("display_name", company_key.capitalize())
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"[{display_name}] Greenhouse error: status {res.status_code}")
            return []
        data = res.json()
        return [
            {
                "id": f"gh_{item['id']}",
                "company": display_name,
                "title": item.get("title", "Unknown Title"),
                "location": item.get("location", {}).get("name", "Remote/Unspecified"),
                "url": item.get("absolute_url", ""),
            }
            for item in data.get("jobs", [])
        ]
    except Exception as e:
        print(f"[{display_name}] Greenhouse exception: {e}")
        return []


def fetch_lever_jobs(company_key, config):
    """Fetch public jobs from Lever ATS."""
    slug = config["slug"]
    display_name = config.get("display_name", company_key.capitalize())
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"[{display_name}] Lever error: status {res.status_code}")
            return []
        data = res.json()
        return [
            {
                "id": f"lever_{item['id']}",
                "company": display_name,
                "title": item.get("text", "Unknown Title"),
                "location": item.get("categories", {}).get("location", "Remote/Unspecified"),
                "url": item.get("hostedUrl", ""),
            }
            for item in data
        ]
    except Exception as e:
        print(f"[{display_name}] Lever exception: {e}")
        return []


def fetch_icims_jobs(company_key, config):
    """Fetch public jobs from an iCIMS search page."""
    display_name = config.get("display_name", company_key.capitalize())
    search_text = config.get("search_text", "software engineer")
    url = (
        f"{config['base_url'].rstrip('/')}/jobs/search?in_iframe=1"
        f"&searchRelation=keyword_all&ss=1&searchKeyword={quote_plus(search_text)}"
    )
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[{display_name}] iCIMS error: status {res.status_code}")
            return []

        jobs = []
        cards = REGEX_ICIMS_CARD.findall(res.text)
        for card in cards:
            title_match = REGEX_ICIMS_TITLE.search(card)
            if not title_match:
                continue

            title = REGEX_TAG_REMOVAL.sub(" ", unescape(title_match.group(2)))
            title = " ".join(title.split())
            location_values = REGEX_ICIMS_LOCATION.findall(card)
            location = ", ".join(
                " ".join(REGEX_TAG_REMOVAL.sub(" ", unescape(value)).split())
                for value in location_values
            )
            job_url = unescape(title_match.group(1)).replace("&amp;", "&")
            job_id = REGEX_ICIMS_JOB_ID.search(job_url)
            jobs.append({
                "id": f"icims_{company_key}_{job_id.group(1) if job_id else job_url}",
                "company": display_name,
                "title": title,
                "location": location or "Remote/Unspecified",
                "url": job_url,
            })
        return jobs
    except Exception as e:
        print(f"[{display_name}] iCIMS exception: {e}")
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
        "limit": config.get("limit", 50),
        "offset": 0,
        "searchText": config.get("search_text", ""),
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[{display_name}] Workday error: status {res.status_code}")
            return []
        data = res.json()
        jobs = []
        for item in data.get("jobPostings", []):
            external_path = item.get("externalPath", "")
            job_url = f"https://{domain}/en-US/{career_site}{external_path}" if external_path else f"https://{domain}"
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
        print(f"[{display_name}] Workday exception: {e}")
        return []


def fetch_eightfold_jobs(company_key, config):
    """Fetch public jobs from Eightfold.ai ATS."""
    domain = config["domain"]
    subdomain = config.get("subdomain", company_key)
    display_name = config.get("display_name", company_key.capitalize())
    search_text = config.get("search_text", "")
    limit = config.get("limit", 50)

    base_url = config.get("base_url", f"https://{subdomain}.eightfold.ai").rstrip("/")
    url = f"{base_url}/api/apply/v2/jobs"

    params = {
        "domain": domain,
        "start": 0,
        "num": limit,
    }
    if search_text:
        params["query"] = search_text

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[{display_name}] Eightfold error: status {res.status_code}")
            return []
        data = res.json()
        jobs = []
        for item in data.get("positions", []):
            job_id = str(item.get("id") or item.get("display_job_id") or "")
            if not job_id:
                continue

            title = item.get("name", "Unknown Title")

            location = item.get("location")
            if not location and isinstance(item.get("locations"), list):
                location = ", ".join(loc for loc in item["locations"] if isinstance(loc, str))
            if not location:
                location = "Remote/Unspecified"

            job_url = item.get("canonical_url") or item.get("canonicalUrl") or item.get("url")
            if not job_url:
                career_portal = config.get("career_url", base_url)
                job_url = f"{career_portal.rstrip('/')}/careers/job/{job_id}?domain={domain}"

            jobs.append({
                "id": f"ef_{subdomain}_{job_id}",
                "company": display_name,
                "title": title,
                "location": location,
                "url": job_url,
            })
        return jobs
    except Exception as e:
        print(f"[{display_name}] Eightfold exception: {e}")
        return []


# ==========================================
# DISCORD NOTIFIER
# ==========================================
def send_discord_alert(job):
    """Sends a rich formatted embed message to Discord with rate-limit retry support."""
    if not discord_is_configured():
        print("❌ ERROR: DISCORD_WEBHOOK_URL is not configured!")
        return False

    payload = {
        "username": "Jobby Finda Bot",
        "embeds": [
            {
                "title": f"🚨 New Role: {job['title']}",
                "url": job["url"],
                "color": 3066993,  # Green
                "fields": [
                    {"name": "Company", "value": job["company"], "inline": True},
                    {"name": "Location", "value": job["location"], "inline": True},
                ],
                "footer": {"text": "Jobby Finda"},
            }
        ],
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)

            # Success
            if res.status_code in (200, 204):
                print(f"✅ Discord alert sent: [{job['company']}] {job['title']}")
                time.sleep(0.5)  # Short pause between posts to stay under 5 req/sec
                return True

            # Rate limited
            elif res.status_code == 429:
                data = res.json()
                wait_time = data.get("retry_after", 1.0) + 0.1
                print(f"⏳ Rate limited by Discord. Waiting {wait_time:.2f}s before retrying...")
                time.sleep(wait_time)

            else:
                print(f"❌ Discord error HTTP {res.status_code}: {res.text}")
                return False

        except Exception as e:
            print(f"❌ Discord exception: {e}")
            return False

    return False

# ==========================================
# STATE MANAGEMENT & MAIN LOOP
# ==========================================
def load_seen_jobs(file_path=None):
    target_file = file_path or HISTORY_FILE
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return {job_id: {} for job_id in data}
                if isinstance(data, dict):
                    return data
                return {}
            except json.JSONDecodeError:
                return {}
    return {}


def save_seen_jobs(seen_ids, file_path=None):
    target_file = file_path or HISTORY_FILE
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(seen_ids, f, indent=2, sort_keys=True)


def clear_seen_jobs(file_path=None, older_than_days=None, backup=True):
    """
    Clears or prunes seen jobs history to reset alert tracking.
    
    Args:
        file_path (str, optional): Path to the history file. Defaults to HISTORY_FILE.
        older_than_days (int, optional): If specified, only removes entries older than N days (based on cached_at).
                                         If None, completely empties the file.
        backup (bool): If True, creates a .bak backup copy before clearing or pruning.
    
    Returns:
        dict: Summary containing counts of cleared and remaining records.
    """
    target_file = file_path or HISTORY_FILE

    if not os.path.exists(target_file):
        print(f"[INFO] No history file found at '{target_file}'. Initializing new empty file.")
        save_seen_jobs({}, target_file)
        return {"cleared": 0, "remaining": 0}

    # Backup existing file before modifications
    if backup:
        backup_file = f"{target_file}.bak"
        try:
            shutil.copy2(target_file, backup_file)
            print(f"[BACKUP] Backup created at '{backup_file}'")
        except Exception as e:
            print(f"[WARNING] Could not create backup: {e}")

    seen_jobs = load_seen_jobs(target_file)
    initial_count = len(seen_jobs)

    if older_than_days is None:
        save_seen_jobs({}, target_file)
        print(f"[RESET] Cleared all {initial_count} seen jobs from '{os.path.basename(target_file)}'.")
        return {"cleared": initial_count, "remaining": 0}
    else:
        cutoff_time = time.time() - (older_than_days * 86400)
        pruned_jobs = {}
        removed_count = 0

        for job_id, meta in seen_jobs.items():
            cached_at = meta.get("cached_at") if isinstance(meta, dict) else None
            if cached_at and cached_at < cutoff_time:
                removed_count += 1
            else:
                pruned_jobs[job_id] = meta

        save_seen_jobs(pruned_jobs, target_file)
        print(
            f"[PRUNE] Pruned {removed_count} jobs older than {older_than_days} days. "
            f"{len(pruned_jobs)} jobs remaining in '{os.path.basename(target_file)}'."
        )
        return {"cleared": removed_count, "remaining": len(pruned_jobs)}


def save_jobs_cache(jobs):
    with open(JOBS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, sort_keys=True)


def get_job_metadata(job, source):
    return {
        "company": job["company"],
        "title": job["title"],
        "location": job["location"],
        "url": job["url"],
        "source": source,
        "cached_at": time.time(),
    }


def _fetch_company_jobs(company_key, config):
    """Fetch jobs from a single company. Used for parallel execution."""
    board_type = config.get("type")
    display_name = config.get("display_name", company_key)

    if board_type == "greenhouse":
        jobs = fetch_greenhouse_jobs(company_key, config)
    elif board_type == "lever":
        jobs = fetch_lever_jobs(company_key, config)
    elif board_type == "icims":
        jobs = fetch_icims_jobs(company_key, config)
    elif board_type == "workday":
        jobs = fetch_workday_jobs(company_key, config)
    elif board_type == "eightfold":
        jobs = fetch_eightfold_jobs(company_key, config)
    else:
        return company_key, display_name, []

    current_time = time.time()
    for job in jobs:
        job["cached_at"] = current_time
    return company_key, display_name, jobs


def main():
    seen_ids = load_seen_jobs()
    print(f"Starting job search... (Loaded {len(seen_ids)} previously seen job IDs)")

    new_jobs_found = []
    pending_ids = set()
    cached_jobs = []

    # Fetch jobs from all companies in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_fetch_company_jobs, company_key, config): company_key
            for company_key, config in TARGET_COMPANIES.items()
        }
        
        for future in as_completed(futures):
            company_key, display_name, jobs = future.result()
            print(f"[{display_name}] Fetched {len(jobs)} total jobs.")
            cached_jobs.extend(jobs)

            # Process jobs from this company
            for job in jobs:
                if job["id"] in seen_ids:
                    if not seen_ids[job["id"]]:
                        seen_ids[job["id"]] = get_job_metadata(job, jobs[0].get("source", "unknown") if jobs else "unknown")
                    continue

                if not is_matching_job(job):
                    continue

                if job["id"] not in pending_ids:
                    new_jobs_found.append((job, company_key))
                    pending_ids.add(job["id"])

    print(f"\nFound {len(new_jobs_found)} new matching role(s). Processing results...")

    # Process new jobs and send alerts
    for job, company_key in new_jobs_found:
        alert_sent = not discord_is_configured() or send_discord_alert(job)
        if not discord_is_configured():
            print(f"ℹ️ Discord not configured; recorded [{job['company']}] {job['title']}")

        if alert_sent:
            config = TARGET_COMPANIES.get(company_key, {})
            board_type = config.get("type", "unknown")
            seen_ids[job["id"]] = get_job_metadata(job, board_type)
            save_seen_jobs(seen_ids)

    save_jobs_cache(cached_jobs)
    save_seen_jobs(seen_ids)
    print("Job check completed successfully!")


def parse_args():
    parser = argparse.ArgumentParser(description="Job board monitor and alert system.")
    parser.add_argument(
        "--clear", "--reset",
        action="store_true",
        dest="clear",
        help="Clear all seen jobs history to reset alerts.",
    )
    parser.add_argument(
        "--prune",
        type=int,
        metavar="DAYS",
        help="Prune seen jobs older than the specified number of days.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help=f"Target seen jobs file path (default: {HISTORY_FILE}).",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a .bak backup file when clearing or pruning.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.clear:
        target_file = args.file or HISTORY_FILE
        clear_seen_jobs(file_path=target_file, backup=not args.no_backup)
    elif args.prune is not None:
        target_file = args.file or HISTORY_FILE
        clear_seen_jobs(file_path=target_file, older_than_days=args.prune, backup=not args.no_backup)
    else:
        main()
