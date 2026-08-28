import streamlit as st

from job_monitor import (
    TARGET_COMPANIES,
    fetch_greenhouse_jobs,
    fetch_lever_jobs,
    fetch_workday_jobs,
)

st.set_page_config(
    page_title="Career Signal",
    page_icon="🔎",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f1ea; }
    [data-testid="stHeader"] { background: rgba(244, 241, 234, 0.9); }
    .hero { padding: 1.5rem 0 1rem; }
    .eyebrow { color: #b24c2f; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; }
    .hero h1 { color: #183b3b; font-family: Georgia, serif; font-size: 3.2rem; margin: 0.2rem 0; }
    .hero p { color: #53605c; font-size: 1.05rem; margin: 0; }
    .result { background: #fffdf8; border-left: 4px solid #d9794f; border-radius: 3px; padding: 1rem 1.2rem; margin: 0.6rem 0; box-shadow: 0 2px 8px rgba(24, 59, 59, 0.07); }
    .result h3 { color: #183b3b; margin: 0 0 0.35rem; font-size: 1.05rem; }
    .meta { color: #68736d; font-size: 0.88rem; }
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
        value="senior, principal, staff, manager, director",
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


def matches(job, role_filters, required_filters, excluded_filters, location_filters):
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()
    searchable = f"{title} {location}"
    return (
        any(term in title for term in role_filters)
        and (not required_filters or all(term in searchable for term in required_filters))
        and not any(term in searchable for term in excluded_filters)
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
    excluded_filters = split_terms(exclude_terms)
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
                    if matches(job, role_filters, required_filters, excluded_filters, location_filters)
                )
            except Exception as error:
                st.warning(f"Could not check {company_key}: {error}")
            progress.progress((index + 1) / len(selected_companies))
        progress.empty()

        results.sort(key=lambda job: (job.get("company", ""), job.get("title", "").lower()))
        st.session_state["results"] = results
        st.session_state["search_summary"] = f"{len(results)} matching roles across {len(selected_companies)} companies"

if "results" in st.session_state:
    st.subheader(st.session_state["search_summary"])
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
