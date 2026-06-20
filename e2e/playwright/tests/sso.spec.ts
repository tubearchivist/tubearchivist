import { test, expect } from '@playwright/test';

const SSO_LABEL = process.env.OIDC_LABEL || 'Log in with SSO';

// Drives the full OIDC redirect flow against the running app + mock IdP:
//   TA login page -> click SSO -> mock-oauth2-server login form ->
//   redirect back to TA callback -> Django session -> authenticated.
// This exercises mozilla-django-oidc under the shipped uvicorn/ASGI server,
// the exact path the old header-forwardauth attempt could not authenticate on.
test('OIDC SSO logs the user in and maps the admin group', async ({ page }) => {
  page.on('console', m => console.log(`[browser] ${m.text()}`));
  page.on('pageerror', e => console.log(`[pageerror] ${e.message}`));

  await page.goto('/login');

  const ssoButton = page.getByRole('button', { name: SSO_LABEL });
  await expect(ssoButton).toBeVisible();

  await Promise.all([
    page.waitForURL(/mock-oidc:8080/, { timeout: 20_000 }),
    ssoButton.click(),
  ]);

  // mock-oauth2-server interactive login: subject + optional claims JSON
  await page.locator('input[name="username"]').fill('e2euser');
  await page
    .locator('textarea[name="claims"]')
    .fill(JSON.stringify({ groups: ['tubearchivist-admins'] }));

  await Promise.all([
    page.waitForURL(url => url.host.includes('tubearchivist'), {
      timeout: 20_000,
    }),
    page.locator('input[type="submit"][value="Sign-in"]').click(),
  ]);

  // Session established: the authenticated account API returns the SSO user,
  // promoted to superuser via the groups claim.
  await expect
    .poll(async () => (await page.request.get('/api/user/account/')).status(), {
      timeout: 20_000,
    })
    .toBe(200);

  const account = await (await page.request.get('/api/user/account/')).json();
  expect(account.name).toBe('e2euser');
  expect(account.is_superuser).toBe(true);
});
