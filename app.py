import json
import os
import re

import streamlit as st

from job_monitor import is_us_location

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

st.set_page_config(
    page_title="Career Signal",
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div class="eyebrow">Career Signal</div>'
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


def get_experience_level(title):
    normalized_title = normalize_text(title)
    if any(pattern.search(normalized_title) for pattern in _EXPERIENCE_LEVEL_PATTERNS["Internships"]):
        return {"Internships"}
    if any(pattern.search(normalized_title) for pattern in _EXPERIENCE_LEVEL_PATTERNS["Seniors"]):
        return {"Seniors"}
    if any(pattern.search(normalized_title) for pattern in _EXPERIENCE_LEVEL_PATTERNS["New grads"]):
        return {"New grads"}
    return {"Experienced"}


def split_terms(value):
    return [term.strip().lower() for term in str(value).split(",") if term.strip()]


def contains_term(searchable_text, term):
    normalized_text = normalize_text(searchable_text)
    normalized_term = normalize_text(term)
    if not normalized_term:
        return False
    # Direct match
    if re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", normalized_text):
        return True
    # Word-by-word token matching for multi-word queries
    term_words = normalized_term.split()
    if len(term_words) > 1:
        return all(bool(re.search(rf"(?<!\w){re.escape(w)}", normalized_text)) for w in term_words)
    return False


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


def matches(job, role_filters, company_filters, required_filters, excluded_filters, selected_levels, location_filters, us_only=False):
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    searchable = f"{company} {title} {location}"

    # Company filter
    if company_filters and company not in company_filters:
        return False

    # Role filter (comma-separated alternatives: matches if any term matches title)
    if role_filters and not any(contains_term(title, term) for term in role_filters):
        return False

    # Must include (matches if all terms appear anywhere in searchable)
    if required_filters and not all(contains_term(searchable, term) for term in required_filters):
        return False

    # Exclude (rejects if any term appears anywhere in searchable)
    if excluded_filters and any(contains_term(searchable, term) for term in excluded_filters):
        return False

    # Experience level
    if selected_levels and not (get_experience_level(title) & set(selected_levels)):
        return False

    # US Only checkbox filter
    if us_only and not is_us_location(location):
        return False

    # Location keyword filters (matches if any location term is present)
    if location_filters and not any(contains_term(location, term) for term in location_filters):
        return False

    return True


all_jobs = load_jobs_cache()
available_companies = sorted(list(set(j.get("company", "") for j in all_jobs if j.get("company"))))

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
    search_button = st.button("Search jobs", type="primary", use_container_width=True)


# Execute search either on button press or initial load if not yet stored
if search_button or "results" not in st.session_state:
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

    # Build readable search summary
    st.session_state["search_summary"] = f"Found {len(results):,} role(s) matching your criteria"

if "results" in st.session_state:
    st.markdown(
        f'<div class="results-heading">{st.session_state["search_summary"]}</div>',
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

    results = st.session_state["results"]
    if not results:
        st.info("No matching roles found. Try broadening keywords, selecting more experience levels, or clearing specific location filters.")
    else:
        for job in results:
            exp_level = list(get_experience_level(job.get("title", "")))[0]
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
