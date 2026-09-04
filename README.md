# Career Signal 🔎

A direct-from-source job monitor and search application that aggregates postings directly from company Applicant Tracking Systems (ATS), filtering out ghost listings and stale aggregator data. It sends automated notifications to Discord and provides an interactive Streamlit web interface for custom searches.

---

## ✨ Features

- **Direct ATS Integration:** Scrapes directly from company career portals without third-party aggregator delay. Supports:
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

## 🚀 Quick Start (Local Setup)

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

## ☁️ Deployment

### Deploy the Web App on Streamlit Community Cloud
1. Push your repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select your repository, set the main file path to `app.py`, and deploy.
4. Customize your public URL in app settings (e.g., `https://your-name.streamlit.app`).

### Automated Monitoring via GitHub Actions
The background scraping and Discord alerting pipeline is pre-configured in `.github/workflows/job_check.yml`:
1. Go to your GitHub repository **Settings** → **Secrets and variables** → **Actions**.
2. Add a new repository secret: `DISCORD_WEBHOOK_URL`.
3. The workflow will automatically run every 4 hours, scrape all configured companies, send alerts, and commit the updated `jobs_cache.json` and `seen_jobs.json`.

---

## ⚙️ Adding New Companies

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

## 💡 Recommended Applying Tools
To speed up submitting applications across multiple career portals, we recommend using the [Simplify Copilot Autofill Extension](https://chromewebstore.google.com/detail/simplify-copilot-autofill/pbanhockgagggenencehbnadejlgchfc).
