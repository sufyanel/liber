# Liber Login Aliases 17.0.1.0.0 - Dale, 23 Oct 2026 meeting

Lets a user sign in with any of their company mailbox addresses (for example dale@mail.globelectric.com or
dale@mail.rbcindustrial.com) as well as their main Odoo login. Every alternative login signs in as the same user
with the same password.

## Set up
Settings > Users > open the user > Alternative Logins tab (administrators only) > add one address per line > Save.

## Rules
- Letter case is ignored.
- An alternative login must be unique and can never be another user's login; a new user login cannot reuse one.
- Odoo's own password check, lockout and two-factor authentication are unchanged.

## Deploy
Python module: push to the repository, then Apps > Update Apps List > install "Liber Login Aliases".

## Tests
6 passed (real web sign-in): main login, aliases in any case, wrong password refused, alias cannot take another
user's login, new login cannot reuse an alias, unknown address refused.
