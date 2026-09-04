---
name: add-companies
description: "Add remote, local, or startup employers to companies.json for job-search expansion, using supported ATS configurations and avoiding duplicates."
user-invocable: true
disable-model-invocation: false
---

# Add Companies

When the user asks to add companies or expand the job search:

1. Read `companies.json` and check every requested company for an existing key.
2. Edit `companies.json` directly when the request is clear. Do not return JSON snippets or instructions for the user to copy and paste.
3. Preserve all existing entries and formatting. Never duplicate an existing company.
4. Use only supported ATS configurations:
   - Greenhouse: `type`, `slug`, `display_name`
   - Lever: `type`, `slug`, `display_name`
   - Workday: `type`, `domain`, `tenant`, `career_site`, `display_name`
   - iCIMS: `type`, `base_url`, `search_text` (optional), `display_name`
   - Eightfold: `type`, `domain`, `subdomain` (optional), `base_url` (optional), `career_url` (optional), `display_name`
5. Verify public ATS details before adding a company. If the ATS or required fields cannot be verified, ask for clarification instead of guessing.
6. Keep remote or location notes in `display_name` only when useful; the monitor's matching rules determine listing eligibility.
7. Validate `companies.json` as JSON after editing.
8. Report which companies were added and which were already present.

## Completion criteria

- The requested companies are added directly to `companies.json`, or clearly reported as already present or blocked by missing ATS details.
- No existing configurations are changed unintentionally.
- No duplicate keys are introduced.
- `companies.json` parses successfully.
