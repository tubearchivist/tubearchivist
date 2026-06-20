# OIDC SSO end-to-end tests

Browser E2E that proves the "Log in with SSO" flow works against the shipped
uvicorn/ASGI server (not just the Django test client). Everything runs in
containers, so nothing is installed on the host.

## Stack

`docker-compose.e2e.yml` brings up:

- **tubearchivist** — the app built from this repo (`TA_LOGIN_AUTH_MODE=oidc_local`)
- **archivist-es / archivist-redis** — required backing services
- **mock-oidc** — `navikt/mock-oauth2-server`, a real OIDC provider (discovery,
  authorize form, token, jwks) that accepts any client/redirect with no config
- **e2e-tests** — Playwright (profile `test`), a container on the same network
  so all OIDC endpoints use docker service names (no localhost host-split)

## Run

```bash
cd e2e

# 1. bring up the app and wait for health
docker compose -f docker-compose.e2e.yml up -d --wait

# 2. run the browser test
docker compose -f docker-compose.e2e.yml --profile test up \
  --abort-on-container-exit --exit-code-from e2e-tests e2e-tests

# 3. tear down
docker compose -f docker-compose.e2e.yml --profile test down -v
```

## Real Authentik (fidelity run)

`mock-oidc` is intentionally swappable. For a high-fidelity run against real
Authentik, see `docker-compose.authentik.yml` (Authentik server + worker +
postgres + redis, provisioned by a bootstrap blueprint). Point the same
`TA_OIDC_*` endpoints at the Authentik service and re-run step 2.
