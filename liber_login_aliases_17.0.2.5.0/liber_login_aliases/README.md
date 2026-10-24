# Liber Login Aliases 17.0.2.3.0 - importable from the frontend

Sign in on any website with a company mailbox address (for example dale@mail.globelectric.com or
dale@mail.rbcindustrial.com) as well as the main Odoo login - same user, same password.

## How it works
On the login page the address typed is looked up; if it is an alternative login, the user's real login is
submitted instead. Odoo then checks the password as usual (its own lockout and two-factor authentication apply).
Data only, no Python: install through Apps > Import Module.

## All websites (17.0.2.1.0)
The alias script is loaded as a site-wide frontend asset, so it runs on the login page of every website - also
where a site has its own edited copy of the login page. The login-page template keeps a backup copy; a guard makes
sure only one runs. Tested with the template copy switched off and an edited login page on one site: aliases
signed in on all three test websites.

## Why it failed on some websites, and the fix (17.0.2.3.0)
A website whose login page was ever edited (Website Builder or a theme) has its own frozen copy of the login
page, and additions to the generic login page never reach that copy. On install / upgrade the module now attaches
its logic to every such site copy. It also has a server-side fallback: when a sign-in fails because the address
typed is an alternative login, Odoo signs in again straight away with the real login - no script, no lookup
request, nothing a proxy can cache. Three independent paths, guarded so they never double-submit.
Tested: with every script switched off and an edited login page on one site, aliases signed in on all three test
websites; with everything on, same result, no errors.

## Privacy (17.0.2.5.0)
The alternative login is translated on the server only. The user's real login is never shown in the browser: not
while signing in, not after a wrong password (the field shows the address the user typed), and there is no public
lookup page. The earlier browser lookup and its page are removed automatically on upgrade.

## Set up
Settings > Users > open the user > Alternative Logins tab (administrators only) > one address per line > Save.
Also listed under Settings > Users & Companies > Alternative Logins.

## Rules
- Letter case is ignored.
- Real logins always win: if an address is already someone's login, it is never redirected to another user.
- If the lookup cannot run, the form is submitted exactly as typed.

## Tested (real browser sign-ins)
Alias on Liber Industrial -> Dale; mixed-case alias -> Dale; main login still works; wrong password refused;
Liz's login wrongly listed as Dale's alias still signs in Liz, and Dale's password on it is refused.
