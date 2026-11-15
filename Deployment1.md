# Phase 5 — Deployment and release guide

## Deployment status

This phase prepares a reproducible container package and a safer private-access layout. It does **not** publish the dashboard or create a public website. No owner-controlled domain, hosting account, identity provider, or legal approval was supplied, so a public deployment would be premature.

The application remains a read-only historical research dashboard. It has no user accounts, role separation, trading capability, or persistent user portfolio database. Anyone admitted by the outer access layer sees the same application.

## Option A — Run the hardened Docker package locally

Requirements: Docker Engine with the Compose plugin.

From the project folder:

```bash
docker compose -f Docker-compose1.yml up --build -d
docker compose ps
docker compose logs -f investment-dashboard
```

Open `http://127.0.0.1:8501` on the host computer. The Compose file binds the host port to loopback only, runs the container as an unprivileged user, uses a read-only root filesystem, drops Linux capabilities, and enables a health check. Stop it with:

```bash
docker compose -f Docker-compose1.yml down
```

Do not change the port mapping to `8501:8501` or `0.0.0.0:8501:8501` on an internet-connected host. Do not expose Streamlit directly to the public internet.

## Option B — Private remote access

For private access while keeping the application on an owner-controlled computer, use an identity-aware tunnel such as Cloudflare Tunnel with Cloudflare Access:

1. Register a domain and add it to an account controlled by the project owner.
2. Configure a Cloudflare Access self-hosted application for a dedicated hostname.
3. Use a default-deny policy and allow only named, trusted identities. Require MFA for those identities.
4. Configure the tunnel to forward to `http://127.0.0.1:8501` on the host.
5. Keep tunnel credentials in the tunnel provider's secret store or a protected local runtime secret file, never in this repository or Git history.
6. Test WebSocket connectivity, session expiry, access denial for an unauthorized identity, and the provider's security headers before sharing the hostname.
7. Keep the host computer and Docker service running while remote access is needed.

Useful official guides:

- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)
- [Cloudflare Access for self-hosted applications](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-application/)
- [GitHub as an identity provider](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/github/)

An authenticated access layer is mandatory before remote use. A tunnel by itself is not authentication.

## Option C — Public multi-user launch (not enabled)

Do not use the current package as an unauthenticated public financial service. Before a public launch, the owner must arrange and verify all of the following:

- Owner-controlled domain, managed hosting, HTTPS, authentication, authorization, and account recovery.
- Legal/privacy review of the privacy notice and terms for the actual jurisdiction, hosting provider, data handling, and intended audience.
- A security review of Streamlit's exposed endpoints, WebSocket behavior, reverse-proxy configuration, security headers, request limits, and denial-of-service controls.
- Provider/data licensing review. The Yahoo Finance chart endpoint is unofficial and may delay, change, rate-limit, or block requests.
- Operational monitoring, log retention limits, backups where applicable, incident response, dependency update policy, and a rollback procedure.
- A user-data design and privacy review before introducing accounts, saved portfolios, or other persistent personal data.
- End-to-end tests of the deployed environment, not only local unit tests.

The app currently has no authentication or separate user/admin roles. A public URL without an independently verified authentication layer is not an acceptable release configuration.

## Release verification

Run locally before packaging:

```bash
python -m pip install -r Requirements1.txt
python -m pip install -r Requirements-dev1.txt
python -m compileall -q .
python -m unittest discover -s tests -v
pip-audit
bandit -q -r Analysis1.py -ll
```

Build and start the container on a machine with Docker:

```bash
docker compose build
docker compose up -d
docker compose ps
```

Confirm the container reports healthy, open the dashboard, fetch a small set of tickers, review each tab, and test the CSV/report downloads. Then stop it with `docker compose -f Docker-compose1.yml down`.

The GitHub Actions workflow runs tests, compilation, dependency auditing, Bandit, and a Docker image build on pushes and pull requests. A successful CI run is necessary but does not replace a deployed-environment security review.

## Provider and calculation limitations

- Yahoo Finance's public chart endpoint is unofficial and not guaranteed by this project.
- Historical returns, risk measures, and the transparent heuristic screen are not forecasts or personalized investment advice.
- The app does not execute trades or provide brokerage connectivity.
- Portfolio simulation is a historical buy-and-hold proxy and does not include periodic rebalancing, fees, taxes, or FX conversion.
- The configured risk-free rate is an assumption, not a live yield.
