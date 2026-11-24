import re


RESUME_CATEGORIES = {
    "Embedded": (
        "embedded",
        "firmware",
        "network engineer",
        "networking engineer",
    ),
    "General": (
        "backend",
        "python developer",
        "software engineering",
        "software developer",
        "software development engineer",
        "software engineer",
    ),
    "AI/ML": (
        "ai engineer",
        "ai engineering",
        "ai/ml",
        "artificial intelligence",
        "data engineer",
        "data engineering",
        "machine learning",
        "ml engineer",
        "mlops",
    ),
}

RESUME_CATEGORY_OPTIONS = (*RESUME_CATEGORIES, "Uncategorized")


def _normalize_title(value):
    return re.sub(r"[^a-z0-9+#]+", " ", str(value).lower()).strip()


RESUME_CATEGORY_PATTERNS = {
    category: [
        re.compile(rf"(?<!\w){re.escape(_normalize_title(term))}(?!\w)")
        for term in terms
    ]
    for category, terms in RESUME_CATEGORIES.items()
}


def get_resume_category(title):
    normalized_title = _normalize_title(title)

    # Prefer specialized resume categories when titles include generic software terms too.
    for category in ("Embedded", "AI/ML", "General"):
        for pattern in RESUME_CATEGORY_PATTERNS[category]:
            if pattern.search(normalized_title):
                return category

    return None
