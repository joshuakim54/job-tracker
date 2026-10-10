from functools import lru_cache
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone

import streamlit as st

PIPELINE_STATUSES = ["New", "Saved", "Applied", "Interview", "Rejected"]
PIPELINE_FILE = os.getenv("JOB_PIPELINE_FILE", os.path.join(os.path.dirname(__file__), "job_pipeline.json"))

EXPERIENCE_LEVEL_TERMS = {
    "Internships": [
        "intern",
        "internship",
        "interns",
        "co op",
        "coop",
        "co-op",
        "student",
        "fellow",
        "fellowship",
        "apprentice",
    ],
    "New grads": [
        "new grad",
        "new grads",
        "new graduate",
        "new graduates",
        "university grad",
        "university graduate",
        "entry level",
        "entry-level",
        "early career",
        "junior",
        "jr",
        "jr.",
        "associate software engineer",
        "associate engineer",
        "associate developer",
        "level 1",
        "level i",
        "swe 1",
        "swe i",
        "sde 1",
        "sde i",
        "software engineer 1",
        "software engineer i",
        "software developer 1",
        "software developer i",
        "engineer 1",
        "engineer i",
        "developer 1",
        "developer i",
        "rotational",
        "campus",
    ],
    "Seniors": [
        "senior",
        "sr",
        "sr.",
        "staff",
        "principal",
        "lead",
        "distinguished",
        "architect",
        "director",
        "vp",
        "head of",
        "head",
        "manager",
        "swe 3",
        "swe iii",
        "sde 3",
        "sde iii",
        "software engineer 3",
        "software engineer iii",
        "software engineer 4",
        "software engineer iv",
        "level 3",
        "level iii",
        "level 4",
        "level iv",
    ],
}

# ==========================================
# GEOGRAPHIC DEFINITIONS FOR STRICT US FILTER
# ==========================================
LOCATION_EXCLUDE = [
    # Canada
    "canada", "canadian", "toronto", "vancouver", "montreal", "montréal",
    "ottawa", "calgary", "edmonton", "quebec", "ontario", "alberta",
    "british columbia", "manitoba", "saskatchewan", "nova scotia",
    "new brunswick", "waterloo", "halifax", "victoria", "winnipeg",
    "mississauga", "brampton", "hamilton", "kitchener", "surrey", "burnaby",
    # UK & Europe
    "uk", "united kingdom", "london", "england", "scotland", "wales",
    "europe", "emea", "germany", "berlin", "munich", "frankfurt",
    "france", "paris", "ireland", "dublin", "poland", "warsaw",
    "krakow", "netherlands", "amsterdam", "spain", "madrid", "barcelona",
    "italy", "milan", "rome", "sweden", "stockholm", "switzerland",
    "zurich", "geneva", "austria", "vienna", "denmark", "copenhagen",
    "lithuania", "vilnius", "romania", "bucharest", "czech", "prague",
    "hungary", "budapest", "portugal", "lisbon", "norway", "oslo",
    "finland", "helsinki", "belgium", "brussels", "greece", "athens",
    # Asia & Pacific
    "india", "bengaluru", "bangalore", "hyderabad", "mumbai", "delhi",
    "pune", "gurgaon", "noida", "chennai", "apac", "australia", "sydney",
    "melbourne", "brisbane", "japan", "tokyo", "china", "beijing",
    "shanghai", "shenzhen", "singapore", "taiwan", "taipei", "korea",
    "seoul", "new zealand", "auckland", "philippines", "manila",
    "vietnam", "indonesia", "jakarta", "malaysia",
    # Middle East & Latin America
    "israel", "tel aviv", "latam", "mexico", "mexico city", "brazil",
    "sao paulo", "argentina", "buenos aires", "colombia", "bogota",
    "chile", "santiago", "costa rica", "dubai", "uae"
]

US_STATE_NAMES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia"
]

US_CITIES_AND_HUBS = [
    "san francisco", "sf", "bay area", "silicon valley", "san jose", "sunnyvale",
    "mountain view", "palo alto", "redwood city", "menlo park", "oakland",
    "seattle", "bellevue", "redmond", "austin", "dallas", "houston",
    "san antonio", "chicago", "new york city", "nyc", "manhattan",
    "brooklyn", "boston", "cambridge", "los angeles", "la", "san diego",
    "denver", "boulder", "atlanta", "philadelphia", "philly", "pittsburgh",
    "washington dc", "dc", "arlington", "reston", "mclean", "baltimore",
    "minneapolis", "salt lake city", "slc", "phoenix", "tempe", "portland",
    "miami", "orlando", "tampa", "nashville", "raleigh", "durham",
    "chapel hill", "cary", "morrisville", "charlotte", "rtp",
    "research triangle"
]

US_STATE_CODES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
]

# Pre-compile regexes
REGEX_WORD_BOUNDARY = r"(?<!\w){}(?!\w)"
_LOCATION_EXCLUDE_REGEX = [re.compile(REGEX_WORD_BOUNDARY.format(re.escape(term)), re.I) for term in LOCATION_EXCLUDE]
_US_STATE_NAMES_REGEX = [re.compile(REGEX_WORD_BOUNDARY.format(re.escape(term)), re.I) for term in US_STATE_NAMES]
_US_CITIES_REGEX = [re.compile(REGEX_WORD_BOUNDARY.format(re.escape(term)), re.I) for term in US_CITIES_AND_HUBS]

_STATE_CODE_PATTERN = rf"(?:,\s*|[-/]\s*|\(\s*|;\s*|\bUS\s*[-/]?\s*)({'|'.join(US_STATE_CODES)})(?:\s*[,;)]|\s+[-/]\s*|\s+(?:USA?|United States)\b|\s*$)"
_STATE_CODE_REGEX = re.compile(_STATE_CODE_PATTERN, re.I)

_US_EXPLICIT_REGEX = re.compile(
    r"(?<!\w)(?:united states|usa|u\.s\.a\.|u\.s\.|us - remote|remote - us|us remote|remote in us|remote in the us|remote, us|remote, united states)(?!\w)",
    re.I
)

_CANADIAN_PROVINCE_CODE_REGEX = re.compile(
    r"\b(?:on|bc|ab|qc|mb|sk|ns|nb|nl|pe)\b(?:\s*,\s*ca\b|\s+only\b)",
    re.I
)


def has_genuine_us_indicator(text):
    if _US_EXPLICIT_REGEX.search(text):
        return True
    if any(r.search(text) for r in _US_CITIES_REGEX):
        return True
    if any(r.search(text) for r in _US_STATE_NAMES_REGEX):
        return True
    match = _STATE_CODE_REGEX.search(text)
    if match:
        code = match.group(1).upper()
        if code == "CA":
            if not any(can_term in text.lower() for can_term in ["toronto", "vancouver", "ontario", "on,", "ottawa", "canada"]):
                return True
        else:
            return True
    if re.search(r"(?<!\w)(?:US|USA|United States)(?!\w)", text):
        return True
    return False


@lru_cache(maxsize=4096)
def is_us_location(location):
    raw_loc = str(location).strip()
    if not raw_loc:
        return False

    norm_loc = unicodedata.normalize('NFKD', raw_loc).encode('ascii', 'ignore').decode('utf-8')

    # Exclude any location containing foreign countries, cities, or provinces (e.g. Canada, UK, India)
    if any(r.search(norm_loc) for r in _LOCATION_EXCLUDE_REGEX):
        return False
    if _CANADIAN_PROVINCE_CODE_REGEX.search(norm_loc):
        return False

    # Must contain a verified US location indicator (US city, state name, or contextual state code)
    return has_genuine_us_indicator(norm_loc)


st.set_page_config(
    page_title="Jobby Finda",
    page_icon="🔎",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #0d1919; }
    [data-testid="stHeader"] { background: rgba(13, 25, 25, 0.9); }
    [data-testid="stSidebar"] { background: #122222; }
    .hero { padding: 1.5rem 0 1rem; }
    .eyebrow { color: #f08a61; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; }
    .hero h1 { color: #e8f1ed; font-family: Georgia, serif; font-size: 3.2rem; margin: 0.2rem 0; }
    .hero p { color: #b5c7c1; font-size: 1.05rem; margin: 0; }
    .results-heading { color: #e8f1ed; font-family: Georgia, serif; font-size: 1.45rem; font-weight: 700; margin: 1.8rem 0 0.8rem; }
    .result { background: #172929; border-left: 4px solid #f08a61; border-radius: 4px; padding: 1rem 1.2rem; margin: 0.7rem 0; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22); }
    .result h3 { color: #e8f1ed; margin: 0 0 0.35rem; font-size: 1.1rem; }
    .result a { color: #ffad86; text-decoration: none; }
    .result a:hover { text-decoration: underline; }
    .meta { color: #b5c7c1; font-size: 0.9rem; display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; margin-top: 0.35rem; }
    .badge { background: #233c3c; color: #a4d4cc; border-radius: 12px; font-size: 0.76rem; padding: 0.15rem 0.65rem; font-weight: 600; display: inline-block; }
    .badge-intern { background: #3b2c4d; color: #d6b4fc; }
    .badge-grad { background: #1e3d36; color: #7fe3c5; }
    .badge-senior { background: #48301f; color: #f9ba8b; }
    .badge-mid { background: #223746; color: #9bc6f2; }
    .digest { background: #1d3532; border: 1px solid #2b5b51; border-radius: 4px; padding: 0.85rem 1rem; margin: 1rem 0; color: #c7e8de; }
    .page-info { color: #b5c7c1; font-size: 0.95rem; display: flex; align-items: center; height: 100%; }
    .page-indicator { text-align: center; color: #e8f1ed; font-size: 0.95rem; font-weight: 600; padding-top: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div class="eyebrow">Jobby Finda</div>'
    "<h1>Find work worth opening.</h1>"
    "<p>Search company career sites directly, including remote roles and internships.</p></div>",
    unsafe_allow_html=True,
)


def normalize_text(value):
    return re.sub(r"[^a-z0-9+#]+", " ", str(value).lower()).strip()


# Pre-compile regex patterns for experience level matching
_EXPERIENCE_LEVEL_PATTERNS = {
    level: [re.compile(rf"(?<!\w){re.escape(normalize_text(term))}(?!\w)") for term in terms]
    for level, terms in EXPERIENCE_LEVEL_TERMS.items()
}


@lru_cache(maxsize=8192)
def get_experience_level(title):
    normalized_title = normalize_text(title)
    if any(pattern.search(normalized_title) for pattern in _EXPERIENCE_LEVEL_PATTERNS["Internships"]):
        return "Internships"
    if any(pattern.search(normalized_title) for pattern in _EXPERIENCE_LEVEL_PATTERNS["Seniors"]):
        return "Seniors"
    if any(pattern.search(normalized_title) for pattern in _EXPERIENCE_LEVEL_PATTERNS["New grads"]):
        return "New grads"
    return "Experienced"


def split_terms(value):
    return [term.strip().lower() for term in str(value).split(",") if term.strip()]


def contains_term(searchable_text, term):
    normalized_text = normalize_text(searchable_text)
    normalized_term = normalize_text(term)
    if not normalized_term or not normalized_text:
        return False
    # Fast path: Substring check in C avoids compiling/running regex for negative matches
    if normalized_term in normalized_text:
        if re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", normalized_text):
            return True
    # Word-by-word token matching for multi-word queries
    term_words = normalized_term.split()
    if len(term_words) > 1:
        return all(w in normalized_text and bool(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", normalized_text)) for w in term_words)
    return False


@st.cache_data(show_spinner=False)
def load_jobs_cache():
    cache_file = os.getenv("JOBS_CACHE_FILE", os.path.join(os.path.dirname(__file__), "jobs_cache.json"))
    try:
        with open(cache_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else data.get("jobs", [])
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, AttributeError):
        st.error("The job cache is unavailable. Please wait for the next scheduled update.")
        return []


@st.cache_data(show_spinner=False)
def get_available_companies(jobs):
    return sorted(list(set(j.get("company", "") for j in jobs if j.get("company"))))


def load_pipeline():
    try:
        with open(PIPELINE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_pipeline(pipeline):
    with open(PIPELINE_FILE, "w", encoding="utf-8") as file:
        json.dump(pipeline, file, indent=2)


def get_job_status(pipeline, job):
    return pipeline.get(str(job.get("id", job.get("url", ""))), {}).get("status", "New")


def update_job_status(pipeline, job, status):
    job_key = str(job.get("id", job.get("url", "")))
    record = pipeline.setdefault(job_key, {})
    record.update({
        "status": status,
        "company": job.get("company", ""),
        "title": job.get("title", ""),
        "url": job.get("url", ""),
        "updated_at": time.time(),
    })
    save_pipeline(pipeline)


def get_pipeline_counts(pipeline, total_jobs):
    """Calculates status counts in O(K) where K is number of tracked pipeline entries."""
    counts = {status: 0 for status in PIPELINE_STATUSES}
    for item in pipeline.values():
        st_val = item.get("status")
        if st_val in counts:
            counts[st_val] += 1
    tracked_non_new = sum(counts[s] for s in PIPELINE_STATUSES if s != "New")
    counts["New"] = max(0, total_jobs - tracked_non_new)
    return counts


def get_new_jobs_today(jobs):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    return [
        job for job in jobs
        if isinstance(job.get("cached_at"), (int, float)) and job["cached_at"] >= today_start
    ]


def matches(job, role_filters, company_filters, required_filters, excluded_filters, selected_levels, location_filters, us_only=False):
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    searchable = f"{company} {title} {location}"

    # Company filter
    if company_filters and company not in company_filters:
        return False

    # Role filter (matches if any term matches title)
    if role_filters and not any(contains_term(title, term) for term in role_filters):
        return False

    # Must include (matches if all terms appear in searchable text)
    if required_filters and not all(contains_term(searchable, term) for term in required_filters):
        return False

    # Exclude (rejects if any term appears anywhere in searchable text)
    if excluded_filters and any(contains_term(searchable, term) for term in excluded_filters):
        return False

    # Experience level: skip if all 4 categories are selected
    if selected_levels and len(selected_levels) < 4:
        if get_experience_level(title) not in selected_levels:
            return False

    # US Only checkbox filter (strictly verified US, excluding Canada and foreign)
    if us_only and not is_us_location(location):
        return False

    # Location keyword filters (matches if any location term is present)
    if location_filters and not any(contains_term(location, term) for term in location_filters):
        return False

    return True


# Load data efficiently (cached)
all_jobs = load_jobs_cache()
available_companies = get_available_companies(all_jobs)
pipeline = load_pipeline()
new_jobs_today = get_new_jobs_today(all_jobs)
status_counts = get_pipeline_counts(pipeline, len(all_jobs))

# Initialize session state for pagination
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

with st.sidebar:
    st.header("Search filters")
    role_terms = st.text_input(
        "Role keywords",
        value="software engineer",
        help="Separate alternatives with commas, such as software engineer, backend, python, or data.",
    )
    selected_companies = st.multiselect(
        "Companies",
        options=available_companies,
        default=[],
        help="Filter by specific companies, or leave empty to search all.",
    )
    experience_levels = st.multiselect(
        "Experience level",
        options=["Internships", "New grads", "Experienced", "Seniors"],
        default=["Internships", "New grads", "Experienced", "Seniors"],
        help="Filter by role seniority level.",
    )
    location_terms = st.text_input(
        "Locations",
        value="",
        placeholder="e.g. remote, raleigh, boston, san francisco, new york",
        help="Optional location keywords (comma-separated). Leave blank to see all locations.",
    )
    us_only_checkbox = st.checkbox(
        "US locations only",
        value=False,
        help="Restrict results strictly to verified US cities and remote US roles.",
    )
    include_terms = st.text_input(
        "Must include",
        value="",
        help="Optional terms that must appear in company, title, or location.",
    )
    exclude_terms = st.text_input(
        "Exclude",
        value="",
        help="Optional terms that must not appear in company, title, or location.",
    )
    pipeline_filter = st.selectbox("Pipeline status", ["All statuses"] + PIPELINE_STATUSES)
    jobs_per_page = st.selectbox("Jobs per page", [25, 50, 100], index=0, help="Fewer jobs per page renders significantly faster.")
    search_button = st.button("Search jobs", type="primary", use_container_width=True)


# Build a signature of current search parameters to detect live filter changes
current_search_params = (
    role_terms,
    tuple(selected_companies),
    tuple(experience_levels),
    location_terms,
    us_only_checkbox,
    include_terms,
    exclude_terms,
)

# Execute search on button press, initial load, OR when any search filter changes
if (
    search_button
    or "results" not in st.session_state
    or st.session_state.get("active_params") != current_search_params
):
    st.session_state["active_params"] = current_search_params
    st.session_state.current_page = 1  # Reset to first page on new search
    role_filters = split_terms(role_terms)
    required_filters = split_terms(include_terms)
    excluded_filters = split_terms(exclude_terms)
    location_filters = split_terms(location_terms)

    results = [
        job
        for job in all_jobs
        if matches(
            job,
            role_filters,
            selected_companies,
            required_filters,
            excluded_filters,
            experience_levels,
            location_filters,
            us_only=us_only_checkbox,
        )
    ]

    results.sort(key=lambda job: job.get("cached_at", 0), reverse=True)
    st.session_state["results"] = results

    # Store search criteria for display
    st.session_state["search_criteria"] = {
        "roles": role_terms or "All Roles",
        "companies": selected_companies or ["All Companies"],
        "experience_levels": experience_levels,
        "locations": location_terms or ("US Only" if us_only_checkbox else "All Locations"),
        "include": include_terms,
        "exclude": exclude_terms,
    }


if "results" in st.session_state:
    base_results = st.session_state["results"]

    # Apply pipeline status filter if active
    if pipeline_filter != "All statuses":
        active_results = [job for job in base_results if get_job_status(pipeline, job) == pipeline_filter]
    else:
        active_results = base_results

    st.markdown(
        f'<div class="digest"><strong>{len(new_jobs_today):,} new jobs today</strong> · '
        f'{status_counts["Saved"]:,} saved · {status_counts["Applied"]:,} applied · '
        f'{status_counts["Interview"]:,} interviews</div>',
        unsafe_allow_html=True,
    )

    search_summary = f"Found {len(active_results):,} role(s) matching your criteria"
    if pipeline_filter != "All statuses":
        search_summary += f" with status '{pipeline_filter}'"
    st.markdown(
        f'<div class="results-heading">{search_summary}</div>',
        unsafe_allow_html=True,
    )

    # Display search criteria expander
    if "search_criteria" in st.session_state:
        criteria = st.session_state["search_criteria"]
        with st.expander("📋 View active search criteria"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Roles:** {criteria['roles']}")
                st.write(f"**Companies:** {', '.join(criteria['companies']) if isinstance(criteria['companies'], list) else criteria['companies']}")
                if criteria["experience_levels"]:
                    st.write(f"**Experience Levels:** {', '.join(criteria['experience_levels'])}")
            with col2:
                st.write(f"**Locations:** {criteria['locations']}")
                if criteria["include"]:
                    st.write(f"**Must Include:** {criteria['include']}")
                if criteria["exclude"]:
                    st.write(f"**Exclude:** {criteria['exclude']}")

    if not active_results:
        st.info("No matching roles found. Try broadening keywords, selecting more experience levels, or clearing specific location filters.")
    else:
        # Pagination calculations
        total_items = len(active_results)
        total_pages = max(1, (total_items + jobs_per_page - 1) // jobs_per_page)
        st.session_state.current_page = min(max(1, st.session_state.current_page), total_pages)
        current_page = st.session_state.current_page

        start_idx = (current_page - 1) * jobs_per_page
        end_idx = min(start_idx + jobs_per_page, total_items)
        page_results = active_results[start_idx:end_idx]

        # Top Pagination Toolbar
        if total_pages > 1:
            p_info, p_prev, p_num, p_next = st.columns([3, 1, 2, 1])
            with p_info:
                st.markdown(
                    f'<div class="page-info">Showing <strong>{start_idx + 1}–{end_idx}</strong> of <strong>{total_items:,}</strong> roles</div>',
                    unsafe_allow_html=True,
                )
            with p_prev:
                if st.button("◀ Prev", disabled=(current_page <= 1), use_container_width=True, key="top_prev"):
                    st.session_state.current_page -= 1
                    st.rerun()
            with p_num:
                st.markdown(
                    f'<div class="page-indicator">Page {current_page} of {total_pages}</div>',
                    unsafe_allow_html=True,
                )
            with p_next:
                if st.button("Next ▶", disabled=(current_page >= total_pages), use_container_width=True, key="top_next"):
                    st.session_state.current_page += 1
                    st.rerun()
        else:
            st.markdown(
                f'<div class="page-info" style="margin-bottom: 0.8rem;">Showing all <strong>{total_items:,}</strong> roles</div>',
                unsafe_allow_html=True,
            )

        # Render only jobs on the current page (Fast DOM rendering!)
        for job in page_results:
            current_status = get_job_status(pipeline, job)
            exp_level = get_experience_level(job.get("title", ""))
            badge_class = {
                "Internships": "badge-intern",
                "New grads": "badge-grad",
                "Seniors": "badge-senior",
                "Experienced": "badge-mid",
            }.get(exp_level, "")

            st.markdown(
                f'<div class="result">'
                f'<h3><a href="{job["url"]}" target="_blank">{job["title"]}</a></h3>'
                f'<div class="meta">'
                f'<strong>{job["company"]}</strong> &nbsp;·&nbsp; <span>{job["location"]}</span>'
                f'<span class="badge {badge_class}">{exp_level}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            status_col, notes_col = st.columns([1, 3])
            with status_col:
                selected_status = st.selectbox(
                    "Pipeline status",
                    PIPELINE_STATUSES,
                    index=PIPELINE_STATUSES.index(current_status),
                    key=f"status_{job.get('id', job.get('url', ''))}",
                    label_visibility="collapsed",
                )
                if selected_status != current_status:
                    update_job_status(pipeline, job, selected_status)
                    st.rerun()
            with notes_col:
                job_key = str(job.get("id", job.get("url", "")))
                current_note = pipeline.get(job_key, {}).get("note", "")
                note = st.text_input(
                    "Notes",
                    value=current_note,
                    placeholder="Add a note",
                    key=f"note_{job_key}",
                    label_visibility="collapsed",
                )
                if note != current_note:
                    pipeline.setdefault(job_key, {}).update({"note": note, "updated_at": time.time()})
                    save_pipeline(pipeline)

        # Bottom Pagination Toolbar
        if total_pages > 1:
            st.markdown("<hr style='border-color: #172929; margin: 1.5rem 0 1rem;' />", unsafe_allow_html=True)
            bp_info, bp_prev, bp_num, bp_next = st.columns([3, 1, 2, 1])
            with bp_info:
                st.markdown(
                    f'<div class="page-info">Page <strong>{current_page}</strong> of <strong>{total_pages}</strong> ({total_items:,} total roles)</div>',
                    unsafe_allow_html=True,
                )
            with bp_prev:
                if st.button("◀ Prev", disabled=(current_page <= 1), use_container_width=True, key="bot_prev"):
                    st.session_state.current_page -= 1
                    st.rerun()
            with bp_num:
                st.markdown(
                    f'<div class="page-indicator">Page {current_page} of {total_pages}</div>',
                    unsafe_allow_html=True,
                )
            with bp_next:
                if st.button("Next ▶", disabled=(current_page >= total_pages), use_container_width=True, key="bot_next"):
                    st.session_state.current_page += 1
                    st.rerun()
