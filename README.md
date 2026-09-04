Hi, I'm Josh! I built this job tracker to solve a common frustration with job hunting: platforms like LinkedIn often have ghost listings and outdated postings. This tool pulls active roles directly from companies' official career pages. While I originally built it for software engineering, I am working on expanding it so friends and family across different career fields can use it too. It sends automated Discord alerts for new postings, but now also includes a clean web interface to make searching and filtering easy for anyone.

---

## Features

- **Direct ATS Integration:** Scrapes directly from company career portals without third-party aggregator delay. Supports: (working on adding more!)
  - **Greenhouse**
  - **Lever**
  - **Workday**
  - **iCIMS**
  - **Eightfold.ai**
- **Streamlit Web GUI:** Interactive search interface with filters for keywords, must-include/exclude terms, locations, and experience tiers.
- **Smart Experience Categorization:** Automatically maps job titles into:
  - **Internships / Co-ops**
  - **New Grads & Early Career** (`associate`, `software engineer 1`, `junior`, `entry-level`)
  - **Experienced**
  - **Seniors & Leads** (`senior`, `staff`, `principal`, `lead`, `architect`)
- **Automated Discord Alerts:** Sends rich embeds to a Discord channel whenever new matching roles are posted.
- **Automated GitHub Actions Pipeline:** Scrapes jobs and updates the persistent cache every 4 hours.

---

## Quick Start (Local Setup)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit Search Web App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to use the search interface.

### 3. Run the Job Monitor Manually (Optional)
To fetch fresh postings and check for new alerts locally:
```bash
# Optional: Set your Discord webhook for notifications
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

python job_monitor.py
```

---


## Adding New Companies

Target companies are configured in [`companies.json`](./companies.json). You can add new employers by specifying their ATS configuration:

```json
{
  "dropbox": {
    "type": "greenhouse",
    "slug": "dropbox",
    "display_name": "Dropbox"
  },
  "spotify": {
    "type": "lever",
    "slug": "spotify",
    "display_name": "Spotify"
  },
  "nvidia": {
    "type": "workday",
    "domain": "nvidia.wd5.myworkdayjobs.com",
    "tenant": "nvidia",
    "career_site": "NVIDIAExternalCareerSite",
    "display_name": "NVIDIA"
  },
  "northropgrumman": {
    "type": "eightfold",
    "domain": "ngc.com",
    "subdomain": "ngc",
    "base_url": "https://jobs.northropgrumman.com",
    "display_name": "Northrop Grumman"
  }
}
```

---

## Recommended Applying Tools
To speed up submitting applications across multiple career portals, I recommend using the [Simplify Copilot Autofill Extension](https://chromewebstore.google.com/detail/simplify-copilot-autofill/pbanhockgagggenencehbnadejlgchfc).
