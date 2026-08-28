import streamlit as st

from job_monitor import (
    TARGET_COMPANIES,
    fetch_greenhouse_jobs,
    fetch_lever_jobs,
    fetch_workday_jobs,
)


EXPERIENCE_LEVEL_TERMS = {
    "Internships": ["intern", "internship", "co-op", "coop"],
    "New grads": ["new grad", "new graduate", "university grad", "entry level", "entry-level", "junior"],
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
    selected_companies = st.multiselect(
        "Companies",
        options=list(TARGET_COMPANIES),
        default=list(TARGET_COMPANIES),
        format_func=lambda key: TARGET_COMPANIES[key].get("display_name", key),
    )
    search_button = st.button("Search career sites", type="primary", use_container_width=True)


def split_terms(value):
    return [term.strip().lower() for term in value.split(",") if term.strip()]


def get_experience_level(title):
    title = title.lower()
    matched_levels = {
        level
        for level, terms in EXPERIENCE_LEVEL_TERMS.items()
        if any(term in title for term in terms)
    }
    if matched_levels:
        return matched_levels
    return {"Experienced"}


def matches(job, role_filters, required_filters, selected_levels, location_filters):
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()
    searchable = f"{title} {location}"
    return (
        any(term in title for term in role_filters)
        and (not required_filters or all(term in searchable for term in required_filters))
        and (not selected_levels or get_experience_level(title) & set(selected_levels))
        and (not location_filters or any(term in location for term in location_filters))
    )


def fetch_jobs(company_key):
    config = TARGET_COMPANIES[company_key]
    board_type = config.get("type")
    if board_type == "greenhouse":
        return fetch_greenhouse_jobs(company_key, config)
    if board_type == "lever":
        return fetch_lever_jobs(company_key, config)
    if board_type == "workday":
        return fetch_workday_jobs(company_key, config)
    return []


if search_button:
    role_filters = split_terms(role_terms)
    required_filters = split_terms(include_terms)
    location_filters = split_terms(location_terms)

    if not role_filters:
        st.error("Enter at least one role keyword.")
    elif not selected_companies:
        st.error("Select at least one company.")
    else:
        results = []
        progress = st.progress(0, text="Checking career sites...")
        for index, company_key in enumerate(selected_companies):
            try:
                jobs = fetch_jobs(company_key)
                results.extend(
                    job
                    for job in jobs
                    if matches(job, role_filters, required_filters, experience_levels, location_filters)
                )
            except Exception as error:
                st.warning(f"Could not check {company_key}: {error}")
            progress.progress((index + 1) / len(selected_companies))
        progress.empty()

        results.sort(key=lambda job: (job.get("company", ""), job.get("title", "").lower()))
        st.session_state["results"] = results
        st.session_state["search_summary"] = f"{len(results)} matching roles across {len(selected_companies)} companies"

if "results" in st.session_state:
    st.markdown(
        f'<div class="results-heading">{st.session_state["search_summary"]}</div>',
        unsafe_allow_html=True,
    )
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
    st.info("Choose your filters, then search the selected company career sites.")
