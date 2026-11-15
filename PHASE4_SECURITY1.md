# Phase 4 — Security, validation, and automated quality gates

## Implemented

- Added strict type/range/finite-number validation for ticker parser limits, network timeout, retry count, retry backoff, initial capital, and portfolio allocations.
- Invalid request settings are rejected before any network request is made.
- Added regression tests for malformed ticker input, non-finite request settings, invalid allocations, and invalid starting capital.
- Added GitHub Actions CI for Python compilation, the unit-test suite, dependency vulnerability auditing (`pip-audit`), and Bandit static analysis of the market-analysis module.
- Added development-only security scanner requirements and expanded ignore rules for local secrets, certificates, databases, and tool caches.

## Security boundaries and remaining release work

- The dashboard is a local, read-only research tool. It does not authenticate users, authorize roles, execute trades, or store account credentials.
- Do not expose Streamlit directly to the public internet. For private remote access, use a managed identity-aware access layer/reverse proxy and HTTPS as described in `Deployment1.md`.
- Keep provider credentials, tunnel tokens, OAuth secrets, and private keys out of source files and Git history. Rotate any credential that has ever been committed.
- The Yahoo Finance chart endpoint is unofficial; its availability and terms are outside this project's control.
- CI dependency auditing can report newly disclosed vulnerabilities and may fail when an installed dependency is affected. Review and update dependencies deliberately rather than suppressing findings.
- Bandit currently scans `Analysis1.py`; `App1.py` contains intentional Streamlit HTML/CSS rendering. Review any dynamic HTML changes manually and never interpolate untrusted input into `unsafe_allow_html=True` content.
- No production hosting, domain, authentication provider, or external security headers were configured as part of this phase.

## Run checks locally

```bash
python -m pip install -r Requirements1.txt
python -m pip install -r Requirements-dev1.txt
python -m compileall -q .
python -m unittest discover -s tests -v
pip-audit
bandit -q -r Analysis1.py -ll
```
