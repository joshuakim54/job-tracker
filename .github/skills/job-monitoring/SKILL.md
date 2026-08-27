---
name: job-monitoring
description: "Run, test, troubleshoot, and generalize the job-monitoring bot for any industry or career field. Use when changing search criteria, adding companies or public ATS sources, validating notifications, deduplicating results, or updating GitHub Actions automation."
argument-hint: "What field, locations, roles, sources, or behavior should the monitor support?"
user-invocable: true
disable-model-invocation: false
---

# Job Monitoring

## Outcome

Maintain a reliable job or opportunity monitor that fetches public listings, applies configurable criteria, sends only actionable Discord alerts, and records processed IDs without exposing secrets.

## Workflow

1. Inspect the current implementation, workflow file, state file, and dependency setup before editing.
2. Run a syntax check and a no-network smoke test before changing behavior:
   - `python -m py_compile job_monitor.py`
   - Exercise matching and state functions with representative local data.
   - Mock HTTP responses and the Discord webhook for fetcher and notification tests.
3. Convert field-specific assumptions into configuration. Keep providers, organizations, keywords, exclusions, locations, experience levels, and delivery settings separate from matching logic. Preserve an explicit provider adapter for each source type.
4. For a new field, ask for or infer:
   - Target role, opportunity type, or category terms.
   - Include and exclude keywords, including seniority and employment type.
   - Allowed locations, remote policy, time zone, or geographic scope.
   - Organizations and their public ATS type or API details.
   - Notification destination and desired alert frequency.
5. Normalize incoming records to a common shape containing a stable `id`, source or organization, title, location, URL, and optional description, salary, date, and employment type. Use provider IDs when available; do not deduplicate by title alone.
6. Test matching boundaries: a positive match, missing fields, excluded terms, case variations, remote and multi-location values, and a near miss. Treat malformed provider data as a logged source failure rather than a whole-run crash.
7. Test notification behavior with a mocked webhook: success, HTTP 204, rate limiting, non-success responses, timeout, missing secret, and an empty result set. Never print or commit webhook URLs or tokens.
8. Test state behavior using a temporary state file: missing file, valid IDs, malformed JSON, repeated listings, newly matching listings, and persistence after a run. Confirm a failed fetch does not incorrectly mark unseen records as processed.
9. Run the bot locally with a test webhook or notifications disabled. Use a temporary state file when possible so real history is not changed:
   - PowerShell: `$env:DISCORD_WEBHOOK_URL = "..."; python job_monitor.py`
   - Verify fetch counts, match counts, alert results, and completion output.
10. Validate GitHub Actions separately. Confirm the workflow installs dependencies, exposes only the required secret, has permission to update state, handles no-change commits, and can be started with `workflow_dispatch`. Review the action log without echoing secret values.
11. After edits, rerun the focused tests, `python -m py_compile job_monitor.py`, and a dry run or mocked end-to-end check. Review `git diff` and confirm only intended files and state changes remain.

## Generalization Rules

- Keep the matching engine field-agnostic; domain-specific terms belong in configuration.
- Prefer structured configuration such as JSON, YAML, or environment variables for user-editable criteria. Validate required keys and report invalid entries clearly.
- Keep source adapters small and consistent. Add a new adapter when a provider has a different API contract rather than scattering provider-specific branches through matching or notification code.
- Make location and eligibility policy explicit. An empty include list should have a documented meaning, not silently match everything.
- Preserve stable IDs and state across runs. If a provider lacks IDs, derive a documented deterministic key from immutable source fields and URL.
- Use request timeouts, bounded retries, clear status logging, and graceful per-source failures.
- Keep notifications concise and escape or truncate untrusted listing text before sending it to Discord.
- Use environment variables or repository secrets for credentials. Local placeholders must fail clearly and safely.

## Completion Checklist

- `SKILL.md` or project changes are scoped to the requested field and sources.
- Matching tests cover both matches and exclusions.
- Fetcher tests cover successful, empty, malformed, and failed responses.
- Notification tests do not make real webhook calls.
- State tests prove duplicates are suppressed and new records persist.
- Python compilation and a mocked end-to-end run pass.
- GitHub Actions configuration is valid and secrets are not hard-coded.
- `git status` shows no unintended generated state or unrelated edits.
