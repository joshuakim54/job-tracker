import json
import os
import re

import streamlit as st

from job_monitor import is_us_location, REGEX_NORMALIZE

EXPERIENCE_LEVEL_TERMS = {
    "Internships": ["intern", "internship", "co-op", "coop"],
    "New grads": [
        "new grad",
        "new graduate",
        "university grad",
        "entry level",
        "entry-level",
        "junior",
        "early career",
        "associate software engineer",
        "software engineer i",
        "software engineer 1",
        "software developer i",
        "software developer 1",
    ],
    "Seniors": ["senior", "staff", "principal", "lead", "distinguished", "architect"],
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
    .result { background: #172929; border-left: 4px solid #f08a61; border-radius: 3px; padding: 1rem 1.2rem; margin: 0.6rem 0; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22); }
    .result h3 { color: #e8f1ed; margin: 0 0 0.35rem; font-size: 1.05rem; }
    .result a { color: #ffad86; }
    .meta { color: #b5c7c1; font-size: 0.88rem; }
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

with st.sidebar:
    st.header("Search filters")
    role_terms = st.text_input(
        "Role keywords",
        value="software engineer",
        help="Separate alternatives with commas, such as data analyst, python, or internship.",
    )
    include_terms = st.text_input(
        "Must include",
        value="",
        help="Optional terms that must appear in the title or location.",
    )
    exclude_terms = st.text_input(
        "Exclude",
        value="",
        help="Optional terms that must not appear in the title or location.",
    )
    experience_levels = st.multiselect(
        "Experience level",
        options=["Internships", "New grads", "Experienced", "Seniors"],
        default=["Experienced"],
        help="Choose one or more groups. Senior-level roles include senior, staff, principal, lead, and architect titles.",
    )
    location_terms = st.text_input(
        "Locations",
        value="remote, united states, usa, raleigh, durham, north carolina",
    )
    search_button = st.button("Search jobs", type="primary", use_container_width=True)


def split_terms(value):
    return [term.strip().lower() for term in value.split(",") if term.strip()]


def normalize_text(value):
    return REGEX_NORMALIZE.sub(" ", str(value).lower()).strip()


def contains_term(text, term):
    normalized_text = normalize_text(text)
    normalized_term = normalize_text(term)
    if not normalized_term:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_term)}(?!\w)", normalized_text) is not None


# Pre-compile regex patterns for experience level matching to improve performance
_EXPERIENCE_LEVEL_PATTERNS = {
    level: [re.compile(rf"(?<!\\w){re.escape(term)}(?!\\w)") for term in terms]
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


def matches(job, role_filters, required_filters, excluded_filters, selected_levels, location_filters):
    title = job.get("title", "")
    location = job.get("location", "")
    searchable = f"{title} {location}"
    return (
        any(contains_term(title, term) for term in role_filters)
        and (not required_filters or all(contains_term(searchable, term) for term in required_filters))
        and not any(contains_term(searchable, term) for term in excluded_filters)
        and (not selected_levels or get_experience_level(title) & set(selected_levels))
        and is_us_location(location)
        and (not location_filters or any(contains_term(location, term) for term in location_filters))
    )


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


if search_button:
    role_filters = split_terms(role_terms)
    required_filters = split_terms(include_terms)
    excluded_filters = split_terms(exclude_terms)
    location_filters = split_terms(location_terms)

    if not role_filters:
        st.error("Enter at least one role keyword.")
    else:
        results = [
            job
            for job in load_jobs_cache()
            if matches(
                job,
                role_filters,
                required_filters,
                excluded_filters,
                experience_levels,
                location_filters,
            )
        ]

        results.sort(key=lambda job: job.get("cached_at", 0), reverse=True)
        st.session_state["results"] = results
        
        # Store search criteria for display
        st.session_state["search_criteria"] = {
            "roles": role_terms,
            "include": include_terms,
            "exclude": exclude_terms,
            "experience_levels": experience_levels,
            "locations": location_terms,
        }
        
        # Build a readable search summary
        experience_label = f" ({', '.join(experience_levels)})" if experience_levels else ""
        st.session_state["search_summary"] = f"Found {len(results)} roles for {role_terms}{experience_label}"

if "results" in st.session_state:
    st.markdown(
        f'<div class="results-heading">{st.session_state["search_summary"]}</div>',
        unsafe_allow_html=True,
    )
    
    # Display search criteria
    if "search_criteria" in st.session_state:
        criteria = st.session_state["search_criteria"]
        with st.expander("📋 View search criteria"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Roles:** {criteria['roles']}")
                if criteria['experience_levels']:
                    st.write(f"**Experience Levels:** {', '.join(criteria['experience_levels'])}")
                if criteria['include']:
                    st.write(f"**Must Include:** {criteria['include']}")
            with col2:
                st.write(f"**Locations:** {criteria['locations']}")
                if criteria['exclude']:
                    st.write(f"**Exclude:** {criteria['exclude']}")
    
    results = st.session_state["results"]
    if not results:
        st.info("No matching roles found. Try broader keywords or locations.")
    else:
        for job in results:
            st.markdown(
                f'<div class="result"><h3><a href="{job["url"]}" target="_blank">{job["title"]}</a></h3>'
                f'<div class="meta">{job["company"]} &nbsp;·&nbsp; {job["location"]}</div></div>',
                unsafe_allow_html=True,
            )
else:
    st.info("Choose your filters, then search the job database.")
